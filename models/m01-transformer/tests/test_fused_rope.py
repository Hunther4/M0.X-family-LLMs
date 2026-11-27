"""Tests for Fused RoPE kernel and RotaryPositionalEmbedding.

Validates:
1. Strict mathematical parity against FP64 eager ground truth in forward and backward
   for float32, bfloat16, and float16.
2. Full RoPE (partial_rotary_factor=1.0) and p-RoPE (partial_rotary_factor=0.5).
3. Zero activation VRAM retention: confirms input activation x is NOT saved in autograd ctx.
4. Clean CPU fallback parity.
5. Non-contiguous input strides and edge cases (single token, large offset).
"""

import os
import pytest
import torch

os.environ["TRITON_CACHE_DIR"] = "/root/.triton/cache"

from src.transformer.config import M01Config
from src.transformer.rope import (
    RotaryPositionalEmbedding,
    FusedRoPEFunction,
    fused_rope,
    _eager_rope_fwd,
    _eager_rope_bwd,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def eager_rope_fp64(x: torch.Tensor, freqs: torch.Tensor, offset: int, rotary_dim: int) -> torch.Tensor:
    """Canonical ground truth computed strictly in float64."""
    batch, seq_len, n_heads, d_head = x.shape
    x64 = x.detach().to(torch.float64).requires_grad_(x.requires_grad)
    x_rot = x64[..., :rotary_dim]
    x_pass = x64[..., rotary_dim:]

    positions = torch.arange(offset, offset + seq_len, device=x.device, dtype=torch.float64)
    freqs64 = freqs[:rotary_dim // 2].to(torch.float64)
    angles = positions.unsqueeze(1) * freqs64.unsqueeze(0)

    cos = torch.cos(angles).unsqueeze(0).unsqueeze(2)
    sin = torch.sin(angles).unsqueeze(0).unsqueeze(2)

    x_even = x_rot[..., 0::2]
    x_odd = x_rot[..., 1::2]

    rot_even = x_even * cos - x_odd * sin
    rot_odd  = x_even * sin + x_odd * cos

    rotated = torch.stack([rot_even, rot_odd], dim=-1).flatten(-2)
    if x_pass.shape[-1] > 0:
        y64 = torch.cat([rotated, x_pass], dim=-1)
    else:
        y64 = rotated
    return y64, x64


@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16, torch.float16])
@pytest.mark.parametrize("partial_rotary_factor", [0.5, 1.0])
@pytest.mark.parametrize("offset", [0, 13])
@pytest.mark.parametrize("shape", [(2, 16, 4, 64), (1, 31, 8, 128)])
def test_fused_rope_parity_vs_fp64(dtype, partial_rotary_factor, offset, shape):
    """Verify strict mathematical parity against eager FP64 in forward and backward."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA/ROCm not available")

    torch.manual_seed(42)
    batch, seq_len, n_heads, d_head = shape
    rotary_dim = int(d_head * partial_rotary_factor)
    if rotary_dim % 2 != 0:
        rotary_dim -= 1
    rotary_dim = max(2, rotary_dim)

    # Compute frequencies
    theta = 10000.0
    freqs = 1.0 / (theta ** (torch.arange(0, rotary_dim, 2, device=DEVICE, dtype=torch.float32) / d_head))

    # Inputs for test
    x = torch.randn(shape, device=DEVICE, dtype=dtype, requires_grad=True)
    dy = torch.randn(shape, device=DEVICE, dtype=dtype)

    # 1. Fused RoPE (Triton)
    y = FusedRoPEFunction.apply(x, freqs, offset, rotary_dim)
    loss = (y * dy).sum()
    loss.backward()

    # 2. FP64 reference forward and backward
    y64, x64 = eager_rope_fp64(x, freqs, offset, rotary_dim)
    loss64 = (y64 * dy.to(torch.float64)).sum()
    loss64.backward()

    # Tolerances based on floating point precision
    if dtype == torch.float32:
        atol, rtol = 2e-5, 2e-5
    elif dtype == torch.bfloat16:
        atol, rtol = 3e-2, 3e-2
    else:  # float16
        atol, rtol = 3e-3, 3e-3

    # Compare forward
    fwd_diff = (y.float() - y64.float()).abs().max().item()
    assert torch.allclose(y.float(), y64.float(), atol=atol, rtol=rtol), (
        f"Forward mismatch for {dtype}, factor={partial_rotary_factor}, offset={offset}: max_diff={fwd_diff}"
    )

    # Compare backward (dx)
    bwd_diff = (x.grad.float() - x64.grad.float()).abs().max().item()
    assert torch.allclose(x.grad.float(), x64.grad.float(), atol=atol, rtol=rtol), (
        f"Backward mismatch for {dtype}, factor={partial_rotary_factor}, offset={offset}: max_diff={bwd_diff}"
    )


def test_fused_rope_zero_vram_activations():
    """Verify that input activation tensor x is NEVER saved in autograd ctx.

    RoPE is an orthogonal unitary rotation: R(θ)^T = R(-θ).
    Backward only requires dy and freqs, achieving 100% RoPE activation VRAM savings.
    """
    if not torch.cuda.is_available():
        pytest.skip("CUDA/ROCm not available")

    x = torch.randn(2, 8, 4, 64, device=DEVICE, dtype=torch.float32, requires_grad=True)
    freqs = torch.randn(32, device=DEVICE, dtype=torch.float32)

    y = FusedRoPEFunction.apply(x, freqs, 0, 64)

    # Inspect autograd saved tensors
    assert hasattr(y.grad_fn, "saved_tensors"), "grad_fn must have saved_tensors"
    saved = y.grad_fn.saved_tensors
    assert len(saved) == 1, f"Expected exactly 1 saved tensor (freqs), got {len(saved)}"
    assert saved[0].data_ptr() == freqs.data_ptr(), "Saved tensor must be freqs"

    # Backward completes correctly
    loss = y.sum()
    loss.backward()
    assert x.grad is not None


@pytest.mark.parametrize("partial_rotary_factor", [0.5, 1.0])
def test_rotary_positional_embedding_module(partial_rotary_factor):
    """Test RotaryPositionalEmbedding module with M01Config."""
    config = M01Config(
        d_model=640,
        n_heads=10,
        rope_theta=10000.0,
    )
    config.partial_rotary_factor = partial_rotary_factor
    rope = RotaryPositionalEmbedding(config)
    if torch.cuda.is_available():
        rope = rope.to(DEVICE)

    x = torch.randn(2, 10, config.n_heads, config.d_head, device=rope.freqs.device, requires_grad=True)
    y = rope(x, offset=5)

    assert y.shape == x.shape
    assert y.dtype == x.dtype

    loss = y.sum()
    loss.backward()
    assert x.grad is not None
    assert x.grad.shape == x.shape


def test_fused_rope_cpu_fallback():
    """Verify that FusedRoPEFunction falls back cleanly to eager execution on CPU."""
    torch.manual_seed(42)
    B, S, H, D = 2, 8, 2, 64
    rotary_dim = 32  # p-RoPE = 0.5
    theta = 10000.0
    freqs = 1.0 / (theta ** (torch.arange(0, rotary_dim, 2, dtype=torch.float32) / D))

    x_cpu = torch.randn(B, S, H, D, device="cpu", dtype=torch.float32, requires_grad=True)
    dy_cpu = torch.randn(B, S, H, D, device="cpu", dtype=torch.float32)

    # Forward on CPU
    y_cpu = FusedRoPEFunction.apply(x_cpu, freqs, 3, rotary_dim)
    assert y_cpu.device.type == "cpu"
    loss_cpu = (y_cpu * dy_cpu).sum()
    loss_cpu.backward()
    assert x_cpu.grad is not None

    # Compare with pure eager reference
    ref_fwd = _eager_rope_fwd(x_cpu, freqs, 3, rotary_dim)
    ref_bwd = _eager_rope_bwd(dy_cpu, freqs, 3, rotary_dim)

    assert torch.allclose(y_cpu, ref_fwd, atol=1e-6)
    assert torch.allclose(x_cpu.grad, ref_bwd, atol=1e-6)


def test_fused_rope_non_contiguous():
    """Verify that non-contiguous inputs (e.g. transposed tensors) execute correctly."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA/ROCm not available")

    # Create non-contiguous tensor by transposing seq_len and n_heads
    x = torch.randn(2, 4, 8, 64, device=DEVICE, dtype=torch.float32).transpose(1, 2)
    assert not x.is_contiguous()

    rotary_dim = 64
    freqs = 1.0 / (10000.0 ** (torch.arange(0, rotary_dim, 2, device=DEVICE, dtype=torch.float32) / 64))

    out = fused_rope(x, freqs, offset=0, rotary_dim=rotary_dim)
    assert out.shape == x.shape

    # Compare against contiguous version
    x_contig = x.contiguous()
    out_contig = fused_rope(x_contig, freqs, offset=0, rotary_dim=rotary_dim)
    assert torch.allclose(out, out_contig, atol=1e-5)


def test_fused_rope_edge_cases():
    """Verify edge cases: single token (seq_len=1), offset=0 identity, and large offset."""
    if not torch.cuda.is_available():
        pytest.skip("CUDA/ROCm not available")

    config = M01Config(d_model=640, n_heads=10)
    rope = RotaryPositionalEmbedding(config).to(DEVICE)

    # 1. offset=0 identity on first position
    x = torch.randn(1, 1, config.n_heads, config.d_head, device=DEVICE)
    y_pos0 = rope(x, offset=0)
    assert torch.allclose(x, y_pos0, atol=1e-5)

    # 2. Large offset (e.g. 65536)
    y_large_offset = rope(x, offset=65536)
    assert not torch.allclose(x, y_large_offset, atol=1e-5)
    assert y_large_offset.shape == x.shape
