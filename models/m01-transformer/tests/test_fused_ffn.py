import pytest
import torch
import torch.nn.functional as F
import os

# Set cache outside of NTFS to prevent Triton compile slowness on WSL2
os.environ["TRITON_CACHE_DIR"] = "/root/.triton/cache"

from transformer.fused_ffn import fused_swiglu, FusedSwiGLUFunction, HAS_TRITON

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def eager_reference_fp64(gate, up):
    """Canonical ground truth evaluated strictly in float64."""
    g64 = gate.detach().to(torch.float64).requires_grad_(True)
    u64 = up.detach().to(torch.float64).requires_grad_(True)
    out64 = F.silu(g64) * u64
    return out64, g64, u64

def test_dtype_and_shape_mismatch():
    """Verify that shape and dtype mismatches are caught early."""
    g = torch.randn(16, 32, device=DEVICE, dtype=torch.float32)
    u_shape = torch.randn(16, 64, device=DEVICE, dtype=torch.float32)
    with pytest.raises(ValueError):
        fused_swiglu(g, u_shape)

    u_dtype = torch.randn(16, 32, device=DEVICE, dtype=torch.bfloat16)
    with pytest.raises(TypeError):
        fused_swiglu(g, u_dtype)

def test_empty_tensor():
    """Verify empty tensor handling without grid launch crashes."""
    g = torch.empty(0, 32, device=DEVICE, dtype=torch.float32, requires_grad=True)
    u = torch.empty(0, 32, device=DEVICE, dtype=torch.float32, requires_grad=True)
    out = fused_swiglu(g, u)
    assert out.numel() == 0
    loss = out.sum()
    loss.backward()
    assert g.grad.shape == g.shape
    assert u.grad.shape == u.shape

@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16, torch.float16])
@pytest.mark.parametrize("shape", [(128, 512), (37, 1337), (4, 16, 256)])
def test_numerical_parity_vs_fp64(dtype, shape):
    """
    Verify numerical parity against eager fp64 reference.
    Kernel error in reduced precision must not exceed eager reduced precision error.
    """
    torch.manual_seed(42)
    gate = torch.randn(shape, device=DEVICE, dtype=dtype, requires_grad=True)
    up = torch.randn(shape, device=DEVICE, dtype=dtype, requires_grad=True)

    # 1. Forward
    out = fused_swiglu(gate, up)
    loss = (out * 0.5).sum()
    loss.backward()

    # 2. Reference in float64
    out64, g64, u64 = eager_reference_fp64(gate, up)
    loss64 = (out64 * 0.5).sum()
    loss64.backward()

    # 3. Eager in same dtype for baseline quantification
    g_eager = gate.detach().clone().requires_grad_(True)
    u_eager = up.detach().clone().requires_grad_(True)
    out_eager = F.silu(g_eager) * u_eager
    (out_eager * 0.5).sum().backward()

    # Metrics
    fwd_err_kernel = (out.float() - out64.float()).abs().max().item()
    fwd_err_eager  = (out_eager.float() - out64.float()).abs().max().item()

    dg_err_kernel = (gate.grad.float() - g64.grad.float()).abs().max().item()
    dg_err_eager  = (g_eager.grad.float() - g64.grad.float()).abs().max().item()

    du_err_kernel = (up.grad.float() - u64.grad.float()).abs().max().item()
    du_err_eager  = (u_eager.grad.float() - u64.grad.float()).abs().max().item()

    # Allow tiny delta margin over eager baseline for different accumulation ordering
    margin = 1e-5 if dtype == torch.float32 else (5e-2 if dtype == torch.bfloat16 else 5e-3)
    assert fwd_err_kernel <= fwd_err_eager + margin
    assert dg_err_kernel <= dg_err_eager + margin
    assert du_err_kernel <= du_err_eager + margin

def test_non_contiguous_inputs():
    """Verify non-contiguous (strided) inputs return correct values."""
    torch.manual_seed(123)
    g_raw = torch.randn(64, 256, device=DEVICE, dtype=torch.float32)
    u_raw = torch.randn(64, 256, device=DEVICE, dtype=torch.float32)

    g_strided = g_raw[:, ::2].clone()
    u_strided = u_raw[:, ::2].clone()
    g_view = g_raw[:, ::2]
    u_view = u_raw[:, ::2]
    assert not g_view.is_contiguous()

    out_contig = fused_swiglu(g_strided, u_strided)
    out_strided = fused_swiglu(g_view, u_view)

    assert torch.allclose(out_contig, out_strided, atol=1e-6)

def test_extreme_values():
    """Verify stability with extreme inputs without unintended NaN/Inf."""
    # In bfloat16, values up to 500 don't overflow
    g = torch.tensor([-500.0, -50.0, 0.0, 50.0, 500.0], device=DEVICE, dtype=torch.bfloat16, requires_grad=True)
    u = torch.tensor([1.0, -1.0, 2.0, -2.0, 1.0], device=DEVICE, dtype=torch.bfloat16, requires_grad=True)

    out = fused_swiglu(g, u)
    assert not torch.isnan(out).any()
    assert not torch.isinf(out).any()

    loss = out.sum()
    loss.backward()
    assert not torch.isnan(g.grad).any()
    assert not torch.isinf(g.grad).any()
