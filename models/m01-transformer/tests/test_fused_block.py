"""Validation tests for Fused Block Kernels (Frente A):
1. FeedForward integration with fused_swiglu and mathematical parity vs FP64.
2. fused_add_rmsnorm exact parity vs residual add + RMSNorm in FP64.
3. Flash Attention execution on AMD ROCm / RDNA 4 (gfx1200) without falling back to MATH.
"""

import os
import pytest
import torch
import torch.nn.functional as F

os.environ["TRITON_CACHE_DIR"] = "/root/.triton/cache"
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

from src.transformer.config import M01Config
from src.transformer.feedforward import FeedForward
from src.transformer.rms_norm import RMSNorm, fused_add_rmsnorm
from src.transformer.attention_backend import AttentionDispatcher, AttentionBackend
from src.transformer.attention import CausalSelfAttention
from src.transformer.kv_cache import MLAKVCache
from src.model.block import TransformerBlock

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ==============================================================================
# 1. FeedForward and Fused SwiGLU Parity Tests
# ==============================================================================

def eager_feedforward_fp64(x, gate_w, up_w, down_w, is_routed=False, limit=None):
    """Canonical FP64 ground truth for FeedForward."""
    x64 = x.detach().to(torch.float64).requires_grad_(True)
    gw64 = gate_w.detach().to(torch.float64)
    uw64 = up_w.detach().to(torch.float64)
    dw64 = down_w.detach().to(torch.float64)

    gate = F.linear(x64, gw64)
    up = F.linear(x64, uw64)

    if is_routed and limit is not None:
        gate = gate.clamp(max=limit)
        up = up.clamp(min=-limit, max=limit)

    h = F.silu(gate) * up
    out = F.linear(h, dw64)
    return out, x64


def test_feedforward_calls_fused_swiglu(monkeypatch):
    """Verify FeedForward explicitly invokes fused_swiglu."""
    config = M01Config(d_model=64, n_heads=4, d_ff=128)
    ff = FeedForward(config).to(DEVICE)
    x = torch.randn(2, 8, 64, device=DEVICE)

    called = False
    import src.transformer.feedforward as ff_mod
    orig_swiglu = ff_mod.fused_swiglu

    def spy_swiglu(g, u):
        nonlocal called
        called = True
        return orig_swiglu(g, u)

    monkeypatch.setattr(ff_mod, "fused_swiglu", spy_swiglu)
    out = ff(x)
    assert called, "FeedForward.forward MUST invoke fused_swiglu"
    assert out.shape == x.shape


@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16, torch.float16])
def test_feedforward_parity_dense_vs_fp64(dtype):
    """Verify FeedForward output and grad parity vs FP64 eager calculation."""
    torch.manual_seed(42)
    config = M01Config(d_model=64, n_heads=4, d_ff=128)
    ff = FeedForward(config, is_routed_expert=False).to(device=DEVICE, dtype=dtype)

    x = torch.randn(2, 16, 64, device=DEVICE, dtype=dtype, requires_grad=True)
    out = ff(x)
    loss = (out * 0.5).sum()
    loss.backward()

    # Canonical FP64 reference
    out64, x64 = eager_feedforward_fp64(
        x, ff.gate_proj.weight, ff.up_proj.weight, ff.down_proj.weight
    )
    loss64 = (out64 * 0.5).sum()
    loss64.backward()

    # Eager baseline in same dtype
    x_e = x.detach().clone().requires_grad_(True)
    g_e = F.linear(x_e, ff.gate_proj.weight)
    u_e = F.linear(x_e, ff.up_proj.weight)
    h_e = F.silu(g_e) * u_e
    out_e = F.linear(h_e, ff.down_proj.weight)
    (out_e * 0.5).sum().backward()

    fwd_err = (out.float() - out64.float()).abs().max().item()
    fwd_err_eager = (out_e.float() - out64.float()).abs().max().item()
    dx_err = (x.grad.float() - x64.grad.float()).abs().max().item()
    dx_err_eager = (x_e.grad.float() - x64.grad.float()).abs().max().item()

    margin = 1e-4 if dtype == torch.float32 else (5e-2 if dtype == torch.bfloat16 else 5e-3)
    assert fwd_err <= fwd_err_eager + margin
    assert dx_err <= dx_err_eager + margin


def test_feedforward_parity_routed_expert_clamped():
    """Verify SwiGLU clamping in routed experts matches FP64 reference."""
    torch.manual_seed(123)
    config = M01Config(d_model=64, n_heads=4, d_ff=128, swiglu_limit=2.0)
    ff = FeedForward(config, is_routed_expert=True).to(device=DEVICE, dtype=torch.float32)

    # Use large inputs to guarantee clamp saturation
    x = torch.randn(2, 16, 64, device=DEVICE, dtype=torch.float32) * 10.0
    out = ff(x)

    out64, _ = eager_feedforward_fp64(
        x, ff.gate_proj.weight, ff.up_proj.weight, ff.down_proj.weight,
        is_routed=True, limit=config.swiglu_limit
    )

    diff = (out.float() - out64.float()).abs().max().item()
    assert diff < 1e-4, f"Clamped FeedForward error {diff} exceeded threshold"


# ==============================================================================
# 2. Fused Add + RMSNorm Parity Tests
# ==============================================================================

def eager_add_rmsnorm_fp64(x, res, gamma, eps=1e-5):
    """Canonical FP64 ground truth for residual addition + RMSNorm."""
    x64 = x.detach().to(torch.float64).requires_grad_(True)
    g64 = gamma.detach().to(torch.float64).requires_grad_(True)
    if res is not None:
        r_in64 = res.detach().to(torch.float64).requires_grad_(True)
        r64 = x64 + r_in64
    else:
        r_in64 = None
        r64 = x64

    var64 = torch.mean(r64 ** 2, dim=-1, keepdim=True)
    rstd64 = torch.rsqrt(var64 + eps)
    y64 = r64 * rstd64 * g64
    return y64, r64, x64, r_in64, g64


@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16, torch.float16])
@pytest.mark.parametrize("shape", [(32, 256), (16, 512), (2, 8, 640)])
def test_fused_add_rmsnorm_parity_vs_fp64(dtype, shape):
    """Verify fused_add_rmsnorm matches FP64 residual addition + RMSNorm."""
    torch.manual_seed(42)
    D = shape[-1]
    eps = 1e-5

    x = torch.randn(shape, device=DEVICE, dtype=dtype, requires_grad=True)
    res = torch.randn(shape, device=DEVICE, dtype=dtype, requires_grad=True)
    gamma = torch.randn(D, device=DEVICE, dtype=dtype, requires_grad=True)

    # 1. Fused kernel execution
    y, r = fused_add_rmsnorm(x, res, gamma, eps=eps)
    loss = (y * 0.5 + r * 0.25).sum()
    loss.backward()

    # 2. FP64 reference
    y64, r64, x64, r_in64, g64 = eager_add_rmsnorm_fp64(x, res, gamma, eps=eps)
    loss64 = (y64 * 0.5 + r64 * 0.25).sum()
    loss64.backward()

    # 3. Eager baseline in same dtype
    x_e = x.detach().clone().requires_grad_(True)
    res_e = res.detach().clone().requires_grad_(True)
    g_e = gamma.detach().clone().requires_grad_(True)
    r_e = x_e + res_e
    var_e = torch.mean(r_e.float() ** 2, dim=-1, keepdim=True)
    rstd_e = torch.rsqrt(var_e + eps)
    y_e = (r_e.float() * rstd_e).to(dtype) * g_e
    (y_e * 0.5 + r_e * 0.25).sum().backward()

    # Parity assertions
    fwd_y_err = (y.float() - y64.float()).abs().max().item()
    fwd_y_eager = (y_e.float() - y64.float()).abs().max().item()

    fwd_r_err = (r.float() - r64.float()).abs().max().item()
    fwd_r_eager = (r_e.float() - r64.float()).abs().max().item()

    dx_err = (x.grad.float() - x64.grad.float()).abs().max().item()
    dx_eager = (x_e.grad.float() - x64.grad.float()).abs().max().item()

    dres_err = (res.grad.float() - r_in64.grad.float()).abs().max().item()
    dres_eager = (res_e.grad.float() - r_in64.grad.float()).abs().max().item()

    dg_err = (gamma.grad.float() - g64.grad.float()).abs().max().item()
    dg_eager = (g_e.grad.float() - g64.grad.float()).abs().max().item()

    margin = 1e-5 if dtype == torch.float32 else (5e-2 if dtype == torch.bfloat16 else 5e-3)
    assert fwd_y_err <= fwd_y_eager + margin
    assert fwd_r_err <= fwd_r_eager + margin
    assert dx_err <= dx_eager + margin
    assert dres_err <= dres_eager + margin
    assert dg_err <= dg_eager + margin


def test_fused_add_rmsnorm_without_residual():
    """Verify fused_add_rmsnorm with residual=None works as pure RMSNorm."""
    shape = (16, 256)
    D = shape[-1]
    x = torch.randn(shape, device=DEVICE, dtype=torch.float32, requires_grad=True)
    gamma = torch.randn(D, device=DEVICE, dtype=torch.float32, requires_grad=True)

    y, r = fused_add_rmsnorm(x, None, gamma, eps=1e-5)
    assert torch.allclose(r, x, atol=1e-6)

    # Reference standard RMSNorm
    norm = RMSNorm(D, eps=1e-5).to(DEVICE)
    norm.gamma.data.copy_(gamma.data)
    y_ref = norm(x)

    assert torch.allclose(y, y_ref, atol=1e-5)


def test_transformer_block_backward_compatibility():
    """Verify TransformerBlock with fused_add_rmsnorm maintains backward compatibility."""
    config = M01Config(d_model=128, n_heads=4, d_ff=256, num_experts=1)
    block = TransformerBlock(config).to(DEVICE)
    x = torch.randn(2, 8, 128, device=DEVICE, requires_grad=True)

    # Standard call: single tensor return
    out = block(x)
    assert isinstance(out, torch.Tensor)
    assert out.shape == x.shape

    loss = out.sum()
    loss.backward()
    assert x.grad is not None
    assert x.grad.shape == x.shape

    # Extended call: return_residual=True
    x2 = torch.randn(2, 8, 128, device=DEVICE)
    res2 = torch.randn(2, 8, 128, device=DEVICE)
    ff_out, updated_res = block(x2, residual=res2, return_residual=True)
    assert isinstance(ff_out, torch.Tensor)
    assert isinstance(updated_res, torch.Tensor)
    assert ff_out.shape == x2.shape
    assert updated_res.shape == x2.shape


# ==============================================================================
# 3. Flash Attention Execution and Validation on GPU
# ==============================================================================

@pytest.mark.skipif(not torch.cuda.is_available(), reason="Flash Attention requires CUDA/ROCm GPU")
def test_flash_attention_gpu_no_fallback_to_math():
    """Flash Attention MUST run on ROCm GPU without falling back to MATH."""
    dispatcher = AttentionDispatcher(preferred_backend=AttentionBackend.FLASH)

    # BF16 on GPU
    q = torch.randn(2, 4, 32, 64, device="cuda", dtype=torch.bfloat16)
    k = torch.randn(2, 4, 32, 64, device="cuda", dtype=torch.bfloat16)
    v = torch.randn(2, 4, 32, 64, device="cuda", dtype=torch.bfloat16)

    out = dispatcher.dispatch(q, k, v, is_causal=True, attn_mask=None)
    assert out.shape == q.shape
    assert dispatcher._warned is False, "Flash Attention fell back to MATH!"

    # FP16 on GPU
    q16 = torch.randn(2, 4, 32, 64, device="cuda", dtype=torch.float16)
    k16 = torch.randn(2, 4, 32, 64, device="cuda", dtype=torch.float16)
    v16 = torch.randn(2, 4, 32, 64, device="cuda", dtype=torch.float16)

    out16 = dispatcher.dispatch(q16, k16, v16, is_causal=True, attn_mask=None)
    assert out16.shape == q16.shape
    assert dispatcher._warned is False, "Flash Attention fell back to MATH!"


@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
def test_flash_attention_validation_incompatible_inputs():
    """Flash Attention MUST raise informative errors for FP32, mask, or CPU."""
    dispatcher = AttentionDispatcher(preferred_backend=AttentionBackend.FLASH)

    # 1. FP32 validation
    q_fp32 = torch.randn(2, 4, 16, 64, device="cuda", dtype=torch.float32)
    k_fp32 = torch.randn(2, 4, 16, 64, device="cuda", dtype=torch.float32)
    v_fp32 = torch.randn(2, 4, 16, 64, device="cuda", dtype=torch.float32)

    with pytest.raises(ValueError, match="requires half-precision"):
        dispatcher.dispatch(q_fp32, k_fp32, v_fp32, is_causal=True)

    # 2. Incompatible explicit attn_mask validation
    q_bf16 = torch.randn(2, 4, 16, 64, device="cuda", dtype=torch.bfloat16)
    mask = torch.ones(1, 1, 16, 16, device="cuda", dtype=torch.bool)

    with pytest.raises(ValueError, match="does not support explicit attn_mask"):
        dispatcher.dispatch(q_bf16, q_bf16, q_bf16, attn_mask=mask)

    # 3. CPU tensor validation
    q_cpu = torch.randn(2, 4, 16, 64, device="cpu", dtype=torch.bfloat16)
    with pytest.raises(RuntimeError, match="requires a CUDA/ROCm GPU device"):
        dispatcher.dispatch(q_cpu, q_cpu, q_cpu, is_causal=True)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
def test_causal_self_attention_flash_execution():
    """Verify CausalSelfAttention runs end-to-end with Flash backend and MLAKVCache."""
    config = M01Config(
        d_model=128,
        n_heads=4,
        attention_backend="flash",
        use_mla=True,
        mla_kv_c_dim=64,
        mla_rope_dim=16,
    )
    attn = CausalSelfAttention(config).to(device="cuda", dtype=torch.bfloat16)

    # 1. Causal attention without KV cache
    x = torch.randn(2, 32, 128, device="cuda", dtype=torch.bfloat16)
    out = attn(x)
    assert out.shape == (2, 32, 128)
    assert attn.attention_dispatcher._warned is False

    # 2. Causal prefill with MLAKVCache (offset=0, q_len=kv_len)
    cache = MLAKVCache(
        max_seq_len=64,
        n_heads=config.n_heads,
        latent_dim=config.mla_kv_c_dim,
        rope_dim=config.d_head_rope,
        device=torch.device("cuda"),
        dtype=torch.bfloat16,
    )
    out_cached = attn(x, kv_cache=cache)
    assert out_cached.shape == (2, 32, 128)
    assert cache.seq_len == 32
    assert attn.attention_dispatcher._warned is False
