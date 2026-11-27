"""Unit tests for surgical fixes and edge cases in src/kernel/ modules:
- RMSNorm empty tensor (x.numel() == 0) and D > 8192 validation
- Cross-Entropy n_valid == 0 autograd connectivity and non-power-of-2 block_v
- RoPE GPU tensor offset handling without CPU-GPU synchronization
- Newton-Schulz configurable compute_dtype (float32, bfloat16)
- AOTriton experimental environment flag and backward compatibility shims
"""

import os
import pytest
import torch
import torch.nn.functional as F

from src.kernel.rms_norm import (
    FusedRMSNormFunction,
    FusedAddRMSNormFunction,
    fused_rmsnorm,
    fused_add_rmsnorm,
    RMSNorm,
)
from src.kernel.cross_entropy import (
    fused_chunked_cross_entropy,
    FusedChunkedCrossEntropyFunction,
    _chunked_cross_entropy_pytorch,
)
from src.kernel.rope import (
    fused_rope,
    FusedRoPEFunction,
    RotaryPositionalEmbedding,
    _eager_rope_fwd,
    _eager_rope_bwd,
)
from src.kernel.newton_schulz import zeropower_via_newtonschulz5
from src.kernel.attention import AttentionDispatcher, AttentionBackend

HAS_CUDA = torch.cuda.is_available()


# =====================================================================
# 1. RMSNorm Edge Cases & Invariants
# =====================================================================

@pytest.mark.parametrize("device", ["cpu"] + (["cuda"] if HAS_CUDA else []))
def test_rmsnorm_empty_tensor_forward_backward(device: str):
    """fused_rmsnorm with x.numel() == 0 must return empty tensor and valid zero gradients."""
    x = torch.empty((0, 64), device=device, requires_grad=True)
    gamma = torch.ones(64, device=device, requires_grad=True)

    y = fused_rmsnorm(x, gamma)
    assert y.shape == (0, 64)
    assert y.device == x.device

    # Backward pass must not fail
    loss = y.sum()
    loss.backward()

    assert x.grad is not None
    assert x.grad.shape == (0, 64)
    assert gamma.grad is not None
    assert gamma.grad.shape == (64,)
    assert (gamma.grad == 0).all()


@pytest.mark.parametrize("device", ["cpu"] + (["cuda"] if HAS_CUDA else []))
@pytest.mark.parametrize("has_residual", [False, True])
def test_fused_add_rmsnorm_empty_tensor_forward_backward(device: str, has_residual: bool):
    """fused_add_rmsnorm with x.numel() == 0 must not raise IndexError on ctx.saved_tensors[1]."""
    x = torch.empty((0, 64), device=device, requires_grad=True)
    residual = torch.empty((0, 64), device=device, requires_grad=True) if has_residual else None
    gamma = torch.ones(64, device=device, requires_grad=True)

    y, out_res = fused_add_rmsnorm(x, residual, gamma)
    assert y.shape == (0, 64)
    assert out_res.shape == (0, 64)

    # Backward pass on both outputs
    loss = y.sum() + out_res.sum()
    loss.backward()

    assert x.grad is not None
    assert x.grad.shape == (0, 64)
    if has_residual:
        assert residual.grad is not None
        assert residual.grad.shape == (0, 64)
    assert gamma.grad is not None
    assert gamma.grad.shape == (64,)
    assert (gamma.grad == 0).all()


def test_rmsnorm_d_dimension_limit_validation():
    """Hidden dimension D > 8192 must raise ValueError to prevent SRAM overflow."""
    D_invalid = 8193
    x = torch.randn(2, D_invalid, device="cpu")
    gamma = torch.ones(D_invalid, device="cpu")

    with pytest.raises(ValueError, match="exceeds maximum supported block size of 8192"):
        fused_rmsnorm(x, gamma)

    with pytest.raises(ValueError, match="exceeds maximum supported block size of 8192"):
        fused_add_rmsnorm(x, None, gamma)


# =====================================================================
# 2. Cross-Entropy Edge Cases & Autograd Connectivity
# =====================================================================

def test_chunked_cross_entropy_pytorch_n_valid_zero_autograd():
    """When n_valid == 0, PyTorch fallback MUST return loss connected to autograd graph."""
    H = torch.randn(4, 16, requires_grad=True)
    W = torch.randn(32, 16, requires_grad=True)
    # All targets are ignored (-100)
    Y = torch.full((4,), -100, dtype=torch.long)

    loss = _chunked_cross_entropy_pytorch(H, W, Y, ignore_index=-100)
    assert loss.item() == 0.0
    assert loss.requires_grad, "Loss must remain connected to computation graph!"

    loss.backward()
    assert H.grad is not None
    assert (H.grad == 0).all()
    assert W.grad is not None
    assert (W.grad == 0).all()


@pytest.mark.skipif(not HAS_CUDA, reason="CUDA required for Triton cross-entropy")
def test_fused_cross_entropy_cuda_n_valid_zero_autograd():
    """When n_valid == 0 on GPU, fused cross-entropy MUST return loss connected to autograd graph."""
    H = torch.randn(4, 16, device="cuda", requires_grad=True)
    W = torch.randn(32, 16, device="cuda", requires_grad=True)
    Y = torch.full((4,), -100, dtype=torch.long, device="cuda")

    # Test mean reduction
    loss_mean = fused_chunked_cross_entropy(H, W, Y, ignore_index=-100, reduction="mean")
    assert loss_mean.item() == 0.0
    assert loss_mean.requires_grad
    loss_mean.backward()
    assert H.grad is not None and (H.grad == 0).all()
    assert W.grad is not None and (W.grad == 0).all()

    # Reset grads
    H.grad = None
    W.grad = None

    # Test sum reduction
    loss_sum = fused_chunked_cross_entropy(H, W, Y, ignore_index=-100, reduction="sum")
    assert loss_sum.item() == 0.0
    assert loss_sum.requires_grad
    loss_sum.backward()
    assert H.grad is not None and (H.grad == 0).all()
    assert W.grad is not None and (W.grad == 0).all()


@pytest.mark.skipif(not HAS_CUDA, reason="CUDA required for Triton cross-entropy")
@pytest.mark.parametrize("block_v", [17, 37, 500, 1000])
def test_cross_entropy_non_power_of_two_block_v(block_v: int):
    """block_v not power of 2 must be safely rounded to power of 2 without Triton errors."""
    H = torch.randn(8, 32, device="cuda", requires_grad=True)
    W = torch.randn(64, 32, device="cuda", requires_grad=True)
    Y = torch.randint(0, 64, (8,), device="cuda")

    loss = fused_chunked_cross_entropy(H, W, Y, block_v=block_v)
    assert torch.isfinite(loss)
    loss.backward()
    assert H.grad is not None
    assert W.grad is not None
    assert torch.isfinite(H.grad).all()
    assert torch.isfinite(W.grad).all()


def test_cross_entropy_invalid_targets_filtering():
    """Targets outside [0, V) must be treated as ignored targets without CUDA assert errors."""
    H = torch.randn(6, 16, requires_grad=True)
    W = torch.randn(20, 16, requires_grad=True)
    # Mix of valid targets, negative targets, out-of-vocab targets, and ignore_index
    Y = torch.tensor([2, -100, -1, 20, 50, 5], dtype=torch.long)

    loss = _chunked_cross_entropy_pytorch(H, W, Y, ignore_index=-100)
    assert torch.isfinite(loss)
    loss.backward()
    assert H.grad is not None
    assert W.grad is not None


# =====================================================================
# 3. RoPE GPU Tensor Offset & Parity
# =====================================================================

@pytest.mark.skipif(not HAS_CUDA, reason="CUDA required for GPU tensor offset test")
def test_rope_gpu_tensor_offset_no_sync():
    """RoPE with GPU tensor offset must match int offset exactly without GPU-CPU sync."""
    torch.manual_seed(42)
    x1 = torch.randn(2, 4, 2, 64, device="cuda", requires_grad=True)
    x2 = x1.detach().clone().requires_grad_(True)
    freqs = 1.0 / (10000.0 ** (torch.arange(0, 32, 2, device="cuda").float() / 64))

    # 1. Forward with standard integer offset
    out_int = fused_rope(x1, freqs, offset=12, rotary_dim=32)
    (out_int * 2.0).sum().backward()

    # 2. Forward with GPU Tensor offset
    offset_gpu = torch.tensor(12, device="cuda", dtype=torch.int64)
    out_gpu = fused_rope(x2, freqs, offset=offset_gpu, rotary_dim=32)
    (out_gpu * 2.0).sum().backward()

    # Parity assertions
    assert torch.allclose(out_int, out_gpu, atol=1e-5)
    assert torch.allclose(x1.grad, x2.grad, atol=1e-5)


def test_rope_eager_tensor_offset_parity():
    """Eager fallback must accept both int and Tensor offset."""
    x = torch.randn(2, 4, 2, 32)
    freqs = 1.0 / (10000.0 ** (torch.arange(0, 16, 2).float() / 32))

    out_int = _eager_rope_fwd(x, freqs, offset=7, rotary_dim=16)
    out_tensor = _eager_rope_fwd(x, freqs, offset=torch.tensor(7), rotary_dim=16)
    assert torch.allclose(out_int, out_tensor)


# =====================================================================
# 4. Newton-Schulz compute_dtype
# =====================================================================

def test_newton_schulz_compute_dtype_fp32_vs_bf16():
    """zeropower_via_newtonschulz5 must accept compute_dtype and preserve output shape and dtype."""
    device = "cuda" if HAS_CUDA else "cpu"
    torch.manual_seed(42)
    G = torch.randn(32, 64, dtype=torch.bfloat16, device=device)

    out_fp32 = zeropower_via_newtonschulz5(G, compute_dtype=torch.float32)
    out_bf16 = zeropower_via_newtonschulz5(G, compute_dtype=torch.bfloat16)

    assert out_fp32.shape == G.shape
    assert out_bf16.shape == G.shape
    assert out_fp32.dtype == torch.bfloat16
    assert out_bf16.dtype == torch.bfloat16

    # Verify both implementations match closely
    diff = (out_fp32.float() - out_bf16.float()).abs().max().item()
    assert diff < 0.05, f"Discrepancy between FP32 and BF16 compute_dtype too high: {diff}"

    # Both must form approximate isometry on smaller dimension (M=32)
    eye = torch.eye(32, device=device, dtype=torch.float32)
    gram_fp32 = torch.matmul(out_fp32.float(), out_fp32.float().t())
    gram_bf16 = torch.matmul(out_bf16.float(), out_bf16.float().t())

    assert (gram_fp32 - eye).abs().max().item() < 0.5
    assert (gram_bf16 - eye).abs().max().item() < 0.5


# =====================================================================
# 5. AOTriton Environment & Shims
# =====================================================================

def test_aotriton_env_variable():
    """TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL must be set to 1."""
    assert os.environ.get("TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL") == "1"


def test_backward_compatibility_shims():
    """Verify that retrocompatible shims in src/transformer/ properly re-export src/kernel/."""
    from src.transformer.rms_norm import RMSNorm as ShimsRMSNorm
    from src.transformer.fused_cross_entropy import FusedCrossEntropyLoss as ShimsCELoss
    from src.transformer.rope import RotaryPositionalEmbedding as ShimsRoPE
    from src.transformer.fused_ffn import fused_swiglu as shims_swiglu
    from src.transformer.attention_backend import AttentionDispatcher as ShimsDispatcher

    assert ShimsRMSNorm is RMSNorm
    assert ShimsRoPE is RotaryPositionalEmbedding
    assert ShimsDispatcher is AttentionDispatcher
