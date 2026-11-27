import pytest
import torch
import os

os.environ["TRITON_CACHE_DIR"] = "/root/.triton/cache"

from transformer.rms_norm import RMSNorm

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def eager_rmsnorm_fp64(x, gamma, eps=1e-5):
    """Canonical ground truth computed strictly in float64."""
    x64 = x.detach().to(torch.float64).requires_grad_(True)
    g64 = gamma.detach().to(torch.float64).requires_grad_(True)
    
    var64 = torch.mean(x64 ** 2, dim=-1, keepdim=True)
    rstd64 = torch.rsqrt(var64 + eps)
    y64 = x64 * rstd64 * g64
    return y64, x64, g64

@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16, torch.float16])
@pytest.mark.parametrize("shape", [(128, 512), (37, 640), (4, 16, 1024)])
def test_rmsnorm_parity_vs_fp64(dtype, shape):
    """Verify forward and backward parity (dx, dgamma) against eager fp64."""
    torch.manual_seed(42)
    D = shape[-1]
    eps = 1e-5

    x = torch.randn(shape, device=DEVICE, dtype=dtype, requires_grad=True)
    gamma = torch.randn(D, device=DEVICE, dtype=dtype, requires_grad=True)

    # 1. Implementation to test
    norm = RMSNorm(D, eps=eps).to(device=DEVICE, dtype=dtype)
    norm.gamma.data.copy_(gamma.data)
    y = norm(x)
    loss = (y * 0.5).sum()
    loss.backward()

    # 2. Reference in float64
    y64, x64, g64 = eager_rmsnorm_fp64(x, gamma, eps=eps)
    loss64 = (y64 * 0.5).sum()
    loss64.backward()

    # 3. Eager baseline in same dtype
    x_eager = x.detach().clone().requires_grad_(True)
    g_eager = gamma.detach().clone().requires_grad_(True)
    var_e = torch.mean(x_eager.float() ** 2, dim=-1, keepdim=True)
    rstd_e = torch.rsqrt(var_e + eps)
    y_eager = (x_eager.float() * rstd_e).to(dtype) * g_eager
    (y_eager * 0.5).sum().backward()

    # Error metrics
    fwd_err = (y.float() - y64.float()).abs().max().item()
    fwd_err_eager = (y_eager.float() - y64.float()).abs().max().item()

    dx_err = (x.grad.float() - x64.grad.float()).abs().max().item()
    dx_err_eager = (x_eager.grad.float() - x64.grad.float()).abs().max().item()

    dg_err = (norm.gamma.grad.float() - g64.grad.float()).abs().max().item()
    dg_err_eager = (g_eager.grad.float() - g64.grad.float()).abs().max().item()

    margin = 1e-5 if dtype == torch.float32 else (5e-2 if dtype == torch.bfloat16 else 5e-3)
    assert fwd_err <= fwd_err_eager + margin
    assert dx_err <= dx_err_eager + margin
    assert dg_err <= dg_err_eager + margin
