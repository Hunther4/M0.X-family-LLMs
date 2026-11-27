"""Unit tests for Newton-Schulz Zeropower Orthogonalization Orientation and Precision.

Tests:
1. Rectangular matrices M < N (e.g. 32x64, 640x1280): verifies X X^T approx I_M.
2. Rectangular matrices M > N (e.g. 64x32, 1280x640): verifies X^T X approx I_N.
3. Square matrices (e.g. 640x640): verifies X X^T approx I.
4. Precision and performance comparison: BF16 pure vs BF16 with internal FP32.
"""

import time
import pytest
import torch

from src.training.optimizer import zeropower_via_newtonschulz5


def _run_pure_bf16_newtonschulz5(G: torch.Tensor, steps: int = 5, eps: float = 1e-7) -> torch.Tensor:
    """Reference pure BF16 implementation for comparison."""
    assert G.ndim in (2, 3)
    is_2d = G.ndim == 2
    X = G.unsqueeze(0) if is_2d else G

    B, M, N = X.shape
    a, b, c = (3.4445, -4.7750, 2.0315)
    X = X.to(dtype=torch.bfloat16)
    norm = torch.linalg.norm(X.float(), dim=(-2, -1), keepdim=True).to(dtype=torch.bfloat16) + eps
    X = X / norm

    transposed = False
    if M > N:
        X = X.transpose(-1, -2)
        transposed = True

    for _ in range(steps):
        A = torch.bmm(X, X.transpose(-1, -2))
        B_mat = b * A + c * torch.bmm(A, A)
        X = a * X + torch.bmm(B_mat, X)

    if transposed:
        X = X.transpose(-1, -2)

    return X.squeeze(0) if is_2d else X


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA/ROCm not available")
class TestNewtonSchulzOrientation:
    device = "cuda"

    @pytest.mark.parametrize("shape", [(32, 64), (640, 1280)])
    def test_orientation_m_less_than_n(self, shape: tuple[int, int]):
        """Rectangular M < N: verify X X^T approx I_M and has smaller error than X^T X."""
        M, N = shape
        torch.manual_seed(42)
        G = torch.randn(M, N, device=self.device, dtype=torch.bfloat16)
        X = zeropower_via_newtonschulz5(G)

        assert X.shape == (M, N)
        assert X.dtype == torch.bfloat16

        prod_m = X.float() @ X.float().T
        eye_m = torch.eye(M, device=self.device)
        err_m = (prod_m - eye_m).abs().max().item()

        prod_n = X.float().T @ X.float()
        eye_n = torch.eye(N, device=self.device)
        err_n = (prod_n - eye_n).abs().max().item()

        # The smaller dimension M must form an approximate isometry: X X^T approx I_M
        assert err_m < 0.5, f"Max error ||XX^T - I_M|| = {err_m} exceeds threshold for shape {shape}"
        assert err_m < err_n, f"Orientation failure: ||XX^T - I_M|| ({err_m}) should be < ||X^TX - I_N|| ({err_n})"

        # Off-diagonal orthogonality check
        off_diag = prod_m - torch.diag(torch.diag(prod_m))
        assert off_diag.abs().mean().item() < 0.05, "Off-diagonal elements not sufficiently orthogonal"

    @pytest.mark.parametrize("shape", [(64, 32), (1280, 640)])
    def test_orientation_m_greater_than_n(self, shape: tuple[int, int]):
        """Rectangular M > N: verify X^T X approx I_N and has smaller error than X X^T."""
        M, N = shape
        torch.manual_seed(42)
        G = torch.randn(M, N, device=self.device, dtype=torch.bfloat16)
        X = zeropower_via_newtonschulz5(G)

        assert X.shape == (M, N)
        assert X.dtype == torch.bfloat16

        prod_n = X.float().T @ X.float()
        eye_n = torch.eye(N, device=self.device)
        err_n = (prod_n - eye_n).abs().max().item()

        prod_m = X.float() @ X.float().T
        eye_m = torch.eye(M, device=self.device)
        err_m = (prod_m - eye_m).abs().max().item()

        # The smaller dimension N must form an approximate isometry: X^T X approx I_N
        assert err_n < 0.5, f"Max error ||X^TX - I_N|| = {err_n} exceeds threshold for shape {shape}"
        assert err_n < err_m, f"Orientation failure: ||X^TX - I_N|| ({err_n}) should be < ||XX^T - I_M|| ({err_m})"

        # Off-diagonal orthogonality check
        off_diag = prod_n - torch.diag(torch.diag(prod_n))
        assert off_diag.abs().mean().item() < 0.05, "Off-diagonal elements not sufficiently orthogonal"

    def test_orientation_square(self):
        """Square 640 x 640: verify X X^T approx I."""
        M, N = 640, 640
        torch.manual_seed(42)
        G = torch.randn(M, N, device=self.device, dtype=torch.bfloat16)
        X = zeropower_via_newtonschulz5(G)

        assert X.shape == (M, N)
        prod = X.float() @ X.float().T
        eye = torch.eye(M, device=self.device)
        max_err = (prod - eye).abs().max().item()

        assert max_err < 0.3, f"Max error {max_err} exceeds threshold for square 640x640"
        off_diag = prod - torch.diag(torch.diag(prod))
        assert off_diag.abs().mean().item() < 0.02, "Off-diagonal elements not sufficiently orthogonal"


def benchmark_fp32_vs_bf16():
    """Detailed benchmark comparing pure BF16 vs BF16 with internal FP32."""
    if not torch.cuda.is_available():
        print("CUDA/ROCm not available")
        return

    device = "cuda"
    shapes = [(32, 64), (640, 1280), (64, 32), (1280, 640), (640, 640)]
    iters = 100

    print("=" * 115)
    print(f"{'Shape':<16} | {'Orient':<8} | {'FP32 max |err|':<16} | {'BF16 max |err|':<16} | {'FP32 Time (us)':<16} | {'BF16 Time (us)':<16} | {'Speedup':<8}")
    print("-" * 115)

    for shape in shapes:
        M, N = shape
        torch.manual_seed(42)
        G = torch.randn(M, N, device=device, dtype=torch.bfloat16)

        # Warmup
        for _ in range(10):
            _ = zeropower_via_newtonschulz5(G)
            _ = _run_pure_bf16_newtonschulz5(G)
        torch.cuda.synchronize()

        # Benchmark FP32 internal
        start_ev = torch.cuda.Event(enable_timing=True)
        end_ev = torch.cuda.Event(enable_timing=True)
        start_ev.record()
        for _ in range(iters):
            out_fp32 = zeropower_via_newtonschulz5(G)
        end_ev.record()
        torch.cuda.synchronize()
        t_fp32_us = (start_ev.elapsed_time(end_ev) / iters) * 1000.0

        # Benchmark pure BF16
        start_ev.record()
        for _ in range(iters):
            out_bf16 = _run_pure_bf16_newtonschulz5(G)
        end_ev.record()
        torch.cuda.synchronize()
        t_bf16_us = (start_ev.elapsed_time(end_ev) / iters) * 1000.0

        # Precision
        if M <= N:
            orient = "XX^T"
            p_fp32 = out_fp32.float() @ out_fp32.float().T
            p_bf16 = out_bf16.float() @ out_bf16.float().T
            eye = torch.eye(M, device=device)
        else:
            orient = "X^TX"
            p_fp32 = out_fp32.float().T @ out_fp32.float()
            p_bf16 = out_bf16.float().T @ out_bf16.float()
            eye = torch.eye(N, device=device)

        err_fp32 = (p_fp32 - eye).abs().max().item()
        err_bf16 = (p_bf16 - eye).abs().max().item()
        speedup = f"{t_fp32_us / t_bf16_us:.2f}x"

        print(f"{str(shape):<16} | {orient:<8} | {err_fp32:<16.6f} | {err_bf16:<16.6f} | {t_fp32_us:<16.2f} | {t_bf16_us:<16.2f} | {speedup:<8}")

    print("=" * 115)


if __name__ == "__main__":
    benchmark_fp32_vs_bf16()
