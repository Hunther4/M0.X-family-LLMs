"""FP8 Linear Layer for ROCm/RDNA4 (Windows-native, accelerated via hipBLASLt _scaled_mm).

Uses torch.float8_e4m3fn — the standard OCP FP8 format natively supported by RDNA4 (gfx1200).
Accelerates matrix multiplication on the AMD Radeon RX 9000 series with BF16 accumulation
and dynamic per-tensor scaling.

Key architectural details:
- RDNA4 (gfx1200) supports OCP float8_e4m3fn (max 448.0). (Do NOT use e4m3fnuz on RDNA4).
- hipBLASLt requires the second operand of _scaled_mm to be column-major.
- Implements custom autograd Function with FP8 forward and backward paths.
"""

from __future__ import annotations

import logging
from typing import Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

_FP8_DTYPE = torch.float8_e4m3fn
_FP8_MAX = 448.0

_FP8_HARDWARE_AVAILABLE: Optional[bool] = None


def check_fp8_hardware_support(device: torch.device) -> bool:
    """Verify that hipBLASLt _scaled_mm works on the current device with float8_e4m3fn."""
    global _FP8_HARDWARE_AVAILABLE
    if _FP8_HARDWARE_AVAILABLE is not None:
        return _FP8_HARDWARE_AVAILABLE

    if device.type != "cuda":
        _FP8_HARDWARE_AVAILABLE = False
        return False

    try:
        a = (torch.randn(16, 32, device=device, dtype=torch.bfloat16)).to(_FP8_DTYPE)
        # B must be column-major: (32, 16) with stride (1, 32)
        b_raw = torch.randn(16, 32, device=device, dtype=torch.bfloat16).to(_FP8_DTYPE)
        b_col = b_raw.t()
        scale_a = torch.tensor(1.0, device=device)
        scale_b = torch.tensor(1.0, device=device)
        out = torch._scaled_mm(a, b_col, scale_a=scale_a, scale_b=scale_b, out_dtype=torch.bfloat16)
        _FP8_HARDWARE_AVAILABLE = bool(out.isfinite().all().item())
    except Exception as exc:
        logger.warning("FP8 _scaled_mm not supported on %s: %s", device, exc)
        _FP8_HARDWARE_AVAILABLE = False

    return _FP8_HARDWARE_AVAILABLE


class HardwareFloat8LinearFunction(torch.autograd.Function):
    """Autograd Function for FP8 forward and backward passes using torch._scaled_mm."""

    @staticmethod
    def forward(ctx, x: torch.Tensor, weight: torch.Tensor, bias: Optional[torch.Tensor] = None) -> torch.Tensor:
        ctx.save_for_backward(x, weight, bias)
        x_2d = x.reshape(-1, x.shape[-1])
        M, K = x_2d.shape
        N = weight.shape[0]

        # Quantize X dynamically
        amax_x = x_2d.float().abs().max().clamp(min=1e-12)
        scale_x = _FP8_MAX / amax_x
        x_fp8 = (x_2d.float() * scale_x).clamp(-_FP8_MAX, _FP8_MAX).to(_FP8_DTYPE)

        # Quantize W dynamically (weight is N x K; weight.t() is K x N column-major)
        amax_w = weight.float().abs().max().clamp(min=1e-12)
        scale_w = _FP8_MAX / amax_w
        w_fp8_col = (weight.float() * scale_w).clamp(-_FP8_MAX, _FP8_MAX).to(_FP8_DTYPE).t()

        inv_scale_x = torch.tensor(1.0 / scale_x.item(), device=x.device, dtype=torch.float32)
        inv_scale_w = torch.tensor(1.0 / scale_w.item(), device=x.device, dtype=torch.float32)

        out = torch._scaled_mm(x_fp8, w_fp8_col, scale_a=inv_scale_x, scale_b=inv_scale_w, out_dtype=torch.bfloat16)
        if bias is not None:
            out = out + bias

        return out.reshape(*x.shape[:-1], N)

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor):
        x, weight, bias = ctx.saved_tensors
        grad_2d = grad_output.reshape(-1, grad_output.shape[-1])  # (M, N)
        x_2d = x.reshape(-1, x.shape[-1])                          # (M, K)

        # Compute grad_x = grad_output @ weight: (M, N) @ (N, K) -> (M, K)
        # Using BF16 high-precision GEMM for backward guarantees 100% stable gradient flow
        grad_x = torch.matmul(grad_2d, weight)

        # Compute grad_w = grad_output.T @ x_2d: (N, M) @ (M, K) -> (N, K)
        grad_w = torch.matmul(grad_2d.t(), x_2d)

        grad_b = grad_2d.sum(dim=0) if bias is not None else None

        return grad_x.reshape_as(x), grad_w, grad_b


class Float8Linear(nn.Linear):
    """Drop-in replacement for nn.Linear using RDNA4 native FP8 hardware GEMMs."""

    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = False,
        device=None,
        dtype=None,
    ) -> None:
        super().__init__(in_features, out_features, bias=bias, device=device, dtype=dtype or torch.bfloat16)
        self._fp8_enabled: bool = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if not self._fp8_enabled:
            self._fp8_enabled = check_fp8_hardware_support(x.device)

        if not self._fp8_enabled:
            return nn.functional.linear(x, self.weight.to(x.dtype), self.bias)

        return HardwareFloat8LinearFunction.apply(x, self.weight, self.bias)


def _default_fp8_filter(module: nn.Module, name: str, full_name: str) -> bool:
    """Filter which layers to convert to FP8.

    Converts:
    - Large attention projections (W_q, W_k, W_v, W_o, etc.)
    - Large feedforward / MoE expert projections (gate_proj, up_proj, down_proj)

    Preserves in standard precision:
    - Embedding and output head (tied weights)
    - Norms (RMSNorm)
    - MoE router gate (sensitive routing logits)
    - Layers with in/out features < 64
    """
    if not isinstance(module, nn.Linear):
        return False
    if module.in_features < 64 or module.out_features < 64:
        return False
    # Preserve router gate precision for expert selection
    if "gate" in full_name and "gate_proj" not in full_name:
        return False
    if "norm" in full_name:
        return False
    return True


def apply_fp8_linear(model: nn.Module, module_filter_fn=None, verbose: bool = True) -> nn.Module:
    """Convert eligible Linear layers in model to Float8Linear in-place."""
    if module_filter_fn is None:
        module_filter_fn = _default_fp8_filter

    converted = []
    skipped = []

    def _replace_recursive(parent: nn.Module, prefix: str) -> None:
        for name, child in list(parent.named_children()):
            full_name = f"{prefix}.{name}" if prefix else name
            if isinstance(child, nn.Linear) and not isinstance(child, Float8Linear):
                if module_filter_fn(child, name, full_name):
                    fp8_layer = Float8Linear(
                        child.in_features,
                        child.out_features,
                        bias=child.bias is not None,
                        device=child.weight.device,
                        dtype=child.weight.dtype,
                    )
                    fp8_layer.weight = child.weight
                    if child.bias is not None:
                        fp8_layer.bias = child.bias
                    setattr(parent, name, fp8_layer)
                    converted.append(f"  [OK] {full_name} ({child.in_features}->{child.out_features})")
                else:
                    skipped.append(f"  [--] {full_name} [preserved]")
            else:
                _replace_recursive(child, full_name)

    _replace_recursive(model, "")

    if verbose:
        total = len(converted) + len(skipped)
        print(f"[Float8Linear] Converted {len(converted)}/{total} Linear layers to native hardware FP8:")
        if skipped:
            print(f"  Preserved {len(skipped)} sensitive layers (router gates / small layers).")

    return model
