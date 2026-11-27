"""RMS Normalization Layer with Triton and PyTorch Autograd Integration.

RMSNorm normalizes inputs by root mean square along the last dimension,
then scales by a learnable gamma parameter. No shift/bias parameter.

Formula: y = (x / sqrt(mean(x^2) + eps)) * gamma
Reference: https://arxiv.org/abs/1910.07467
"""

from typing import Optional, Tuple
import torch
import torch.nn as nn
from torch import Tensor

try:
    import triton
    import triton.language as tl
    HAS_TRITON = True
except ImportError:
    triton = None
    tl = None
    HAS_TRITON = False

if HAS_TRITON:
    @triton.jit
    def _rmsnorm_fwd_kernel(
        X_ptr, Y_ptr, W_ptr, RSTD_ptr,
        stride_x_row, stride_y_row,
        D: tl.int64,
        eps: tl.float32,
        BLOCK_SIZE: tl.constexpr,
    ):
        row_idx = tl.program_id(0).to(tl.int64)
        row_x_ptr = X_ptr + row_idx * stride_x_row
        row_y_ptr = Y_ptr + row_idx * stride_y_row

        cols = tl.arange(0, BLOCK_SIZE)
        mask = cols < D

        # Upcast to float32 for reduction and variance
        x = tl.load(row_x_ptr + cols, mask=mask, other=0.0).to(tl.float32)
        w = tl.load(W_ptr + cols, mask=mask, other=0.0).to(tl.float32)

        var = tl.sum(x * x, axis=0) / D
        rstd = 1.0 / tl.sqrt(var + eps)
        tl.store(RSTD_ptr + row_idx, rstd)

        # LLaMA-style: cast normalized activation to weight dtype before scaling
        x_hat = (x * rstd).to(W_ptr.dtype.element_ty)
        y = x_hat * w
        tl.store(row_y_ptr + cols, y, mask=mask)

    @triton.jit
    def _rmsnorm_bwd_kernel(
        DY_ptr, X_ptr, W_ptr, RSTD_ptr, DX_ptr, PARTIAL_DW_ptr,
        stride_x_row, stride_dx_row, stride_dy_row,
        M: tl.int64,
        D: tl.int64,
        ROWS_PER_PROGRAM: tl.int64,
        BLOCK_SIZE: tl.constexpr,
    ):
        pid = tl.program_id(0).to(tl.int64)
        cols = tl.arange(0, BLOCK_SIZE)
        mask = cols < D

        w = tl.load(W_ptr + cols, mask=mask, other=0.0).to(tl.float32)

        start_row = pid * ROWS_PER_PROGRAM
        end_row = tl.minimum(start_row + ROWS_PER_PROGRAM, M)

        acc_dw = tl.zeros([BLOCK_SIZE], dtype=tl.float32)

        # Loop over assigned rows for this program chunk
        for r in range(start_row, end_row):
            row_x_ptr = X_ptr + r * stride_x_row
            row_dx_ptr = DX_ptr + r * stride_dx_row
            row_dy_ptr = DY_ptr + r * stride_dy_row

            dy = tl.load(row_dy_ptr + cols, mask=mask, other=0.0).to(tl.float32)
            x = tl.load(row_x_ptr + cols, mask=mask, other=0.0).to(tl.float32)
            rstd = tl.load(RSTD_ptr + r).to(tl.float32)

            # dx_i = rstd * (dy_i * w_i - (rstd^2 / D) * x_i * sum_j(dy_j * w_j * x_j))
            dy_w = dy * w
            sum_dy_w_x = tl.sum(dy_w * x, axis=0)
            c = (rstd * rstd / D) * sum_dy_w_x
            dx = rstd * (dy_w - c * x)
            tl.store(row_dx_ptr + cols, dx.to(DX_ptr.dtype.element_ty), mask=mask)

            # Accumulate partial dgamma in registers across rows
            x_hat = x * rstd
            acc_dw += dy * x_hat

        # Store exactly 1 accumulated vector per program (not per row)
        tl.store(PARTIAL_DW_ptr + pid * D + cols, acc_dw, mask=mask)

    @triton.jit
    def _fused_add_rmsnorm_fwd_kernel(
        X_ptr, RES_ptr, Y_ptr, OUT_RES_ptr, W_ptr, RSTD_ptr,
        stride_x_row, stride_res_row, stride_y_row, stride_out_res_row,
        D: tl.int64,
        eps: tl.float32,
        HAS_RESIDUAL: tl.constexpr,
        BLOCK_SIZE: tl.constexpr,
    ):
        row_idx = tl.program_id(0).to(tl.int64)
        row_x_ptr = X_ptr + row_idx * stride_x_row
        row_y_ptr = Y_ptr + row_idx * stride_y_row
        row_out_res_ptr = OUT_RES_ptr + row_idx * stride_out_res_row

        cols = tl.arange(0, BLOCK_SIZE)
        mask = cols < D

        # Upcast to float32 for reduction and variance
        x = tl.load(row_x_ptr + cols, mask=mask, other=0.0).to(tl.float32)
        if HAS_RESIDUAL:
            row_res_ptr = RES_ptr + row_idx * stride_res_row
            res = tl.load(row_res_ptr + cols, mask=mask, other=0.0).to(tl.float32)
            r = x + res
        else:
            r = x

        # Store updated residual r back to global memory in output residual dtype
        tl.store(row_out_res_ptr + cols, r.to(OUT_RES_ptr.dtype.element_ty), mask=mask)

        w = tl.load(W_ptr + cols, mask=mask, other=0.0).to(tl.float32)
        var = tl.sum(r * r, axis=0) / D
        rstd = 1.0 / tl.sqrt(var + eps)
        tl.store(RSTD_ptr + row_idx, rstd)

        # LLaMA-style: cast normalized activation to weight dtype before scaling
        r_hat = (r * rstd).to(W_ptr.dtype.element_ty)
        y = r_hat * w
        tl.store(row_y_ptr + cols, y, mask=mask)

    @triton.jit
    def _fused_add_rmsnorm_bwd_kernel(
        DY_ptr, DR_IN_ptr, R_ptr, W_ptr, RSTD_ptr, DX_ptr, DRES_ptr, PARTIAL_DW_ptr,
        stride_dy_row, stride_dr_in_row, stride_r_row, stride_dx_row, stride_dres_row,
        M: tl.int64,
        D: tl.int64,
        ROWS_PER_PROGRAM: tl.int64,
        HAS_DR_IN: tl.constexpr,
        HAS_DRES: tl.constexpr,
        BLOCK_SIZE: tl.constexpr,
    ):
        pid = tl.program_id(0).to(tl.int64)
        cols = tl.arange(0, BLOCK_SIZE)
        mask = cols < D

        w = tl.load(W_ptr + cols, mask=mask, other=0.0).to(tl.float32)

        start_row = pid * ROWS_PER_PROGRAM
        end_row = tl.minimum(start_row + ROWS_PER_PROGRAM, M)

        acc_dw = tl.zeros([BLOCK_SIZE], dtype=tl.float32)

        for r_idx in range(start_row, end_row):
            row_dy_ptr = DY_ptr + r_idx * stride_dy_row
            row_r_ptr = R_ptr + r_idx * stride_r_row
            row_dx_ptr = DX_ptr + r_idx * stride_dx_row

            dy = tl.load(row_dy_ptr + cols, mask=mask, other=0.0).to(tl.float32)
            r = tl.load(row_r_ptr + cols, mask=mask, other=0.0).to(tl.float32)
            rstd = tl.load(RSTD_ptr + r_idx).to(tl.float32)

            # Gradient w.r.t r before normalization:
            # dr_norm = rstd * (dy * w - (rstd^2 / D) * r * sum(dy * w * r))
            dy_w = dy * w
            sum_dy_w_r = tl.sum(dy_w * r, axis=0)
            c = (rstd * rstd / D) * sum_dy_w_r
            dr_norm = rstd * (dy_w - c * r)

            if HAS_DR_IN:
                row_dr_in_ptr = DR_IN_ptr + r_idx * stride_dr_in_row
                dr_in = tl.load(row_dr_in_ptr + cols, mask=mask, other=0.0).to(tl.float32)
                dr_total = dr_norm + dr_in
            else:
                dr_total = dr_norm

            tl.store(row_dx_ptr + cols, dr_total.to(DX_ptr.dtype.element_ty), mask=mask)

            if HAS_DRES:
                row_dres_ptr = DRES_ptr + r_idx * stride_dres_row
                tl.store(row_dres_ptr + cols, dr_total.to(DRES_ptr.dtype.element_ty), mask=mask)

            # Accumulate partial dgamma in registers across rows
            r_hat = r * rstd
            acc_dw += dy * r_hat

        # Store exactly 1 accumulated vector per program (compact [num_programs, D])
        tl.store(PARTIAL_DW_ptr + pid * D + cols, acc_dw, mask=mask)

else:
    _rmsnorm_fwd_kernel = None
    _rmsnorm_bwd_kernel = None
    _fused_add_rmsnorm_fwd_kernel = None
    _fused_add_rmsnorm_bwd_kernel = None


class FusedRMSNormFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x: Tensor, gamma: Tensor, eps: float = 1e-5) -> Tensor:
        orig_shape = x.shape
        D = orig_shape[-1] if len(orig_shape) > 0 else 0
        if D > 8192:
            raise ValueError(
                f"Hidden dimension D={D} exceeds maximum supported block size of 8192 "
                f"for SRAM reduction in fused RMSNorm."
            )

        if x.numel() == 0:
            ctx.is_empty = True
            ctx.orig_shape = orig_shape
            ctx.save_for_backward(x, gamma)
            return torch.empty_like(x)

        ctx.is_empty = False
        x_flat = x.contiguous().view(-1, D)
        gamma_flat = gamma.contiguous()
        M = x_flat.shape[0]

        use_triton = HAS_TRITON and x.is_cuda
        ctx.use_triton = use_triton
        ctx.orig_shape = orig_shape
        ctx.eps = eps

        if use_triton:
            y = torch.empty_like(x_flat)
            rstd = torch.empty(M, device=x.device, dtype=torch.float32)
            BLOCK_SIZE = triton.next_power_of_2(D)
            num_warps = 4 if D <= 2048 else 8

            _rmsnorm_fwd_kernel[(M,)](
                x_flat, y, gamma_flat, rstd,
                x_flat.stride(0), y.stride(0),
                D, eps,
                BLOCK_SIZE=BLOCK_SIZE,
                num_warps=num_warps,
            )
            ctx.save_for_backward(x_flat, gamma_flat, rstd)
            return y.view(orig_shape)
        else:
            x_fp32 = x_flat.float()
            rms = torch.sqrt(torch.mean(x_fp32 ** 2, dim=-1, keepdim=True) + eps)
            normalized = (x_fp32 / rms).to(dtype=x.dtype)
            y = normalized * gamma_flat.to(dtype=x.dtype)
            ctx.save_for_backward(x_flat, gamma_flat)
            return y.view(orig_shape)

    @staticmethod
    def backward(ctx, dy: Tensor) -> Tuple[Tensor, Tensor, None]:
        if getattr(ctx, "is_empty", False) or dy.numel() == 0:
            if len(ctx.saved_tensors) >= 2:
                x_saved, gamma_saved = ctx.saved_tensors
                return torch.zeros_like(x_saved), torch.zeros_like(gamma_saved), None
            orig_shape = getattr(ctx, "orig_shape", dy.shape)
            return torch.zeros_like(dy).view(orig_shape), torch.zeros(dy.shape[-1], dtype=dy.dtype, device=dy.device), None

        orig_shape = ctx.orig_shape
        dy_flat = dy.contiguous().view(-1, orig_shape[-1])
        M, D = dy_flat.shape

        if ctx.use_triton:
            x_flat, gamma_flat, rstd = ctx.saved_tensors
            dx = torch.empty_like(x_flat)

            # Cap programs to 64-128 to keep partial_dw compact in VRAM (~1-2 MB total)
            num_programs = min(128, M)
            rows_per_program = triton.cdiv(M, num_programs)
            partial_dw = torch.empty((num_programs, D), device=dy.device, dtype=torch.float32)

            BLOCK_SIZE = triton.next_power_of_2(D)
            num_warps = 4 if D <= 2048 else 8

            _rmsnorm_bwd_kernel[(num_programs,)](
                dy_flat, x_flat, gamma_flat, rstd, dx, partial_dw,
                x_flat.stride(0), dx.stride(0), dy_flat.stride(0),
                M, D, rows_per_program,
                BLOCK_SIZE=BLOCK_SIZE,
                num_warps=num_warps,
            )
            # Deterministic reduction of only num_programs rows in PyTorch
            dgamma = partial_dw.sum(dim=0).to(gamma_flat.dtype)
            return dx.view(orig_shape), dgamma, None
        else:
            x_flat, gamma_flat = ctx.saved_tensors
            x_fp32 = x_flat.float()
            dy_fp32 = dy_flat.float()
            g_fp32 = gamma_flat.float()

            rms = torch.sqrt(torch.mean(x_fp32 ** 2, dim=-1, keepdim=True) + ctx.eps)
            rstd = 1.0 / rms

            dy_g = dy_fp32 * g_fp32
            sum_dy_g_x = (dy_g * x_fp32).sum(dim=-1, keepdim=True)
            dx = rstd * (dy_g - (rstd ** 2 / D) * x_fp32 * sum_dy_g_x)

            x_hat = x_fp32 * rstd
            dgamma = (dy_fp32 * x_hat).sum(dim=0)

            return dx.to(dy.dtype).view(orig_shape), dgamma.to(gamma_flat.dtype), None


def fused_rmsnorm(x: Tensor, gamma: Tensor, eps: float = 1e-5) -> Tensor:
    return FusedRMSNormFunction.apply(x, gamma, eps)


class FusedAddRMSNormFunction(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx,
        x: Tensor,
        residual: Optional[Tensor],
        gamma: Tensor,
        eps: float = 1e-5,
    ) -> Tuple[Tensor, Tensor]:
        orig_shape = x.shape
        D = orig_shape[-1] if len(orig_shape) > 0 else 0
        if D > 8192:
            raise ValueError(
                f"Hidden dimension D={D} exceeds maximum supported block size of 8192 "
                f"for SRAM reduction in fused RMSNorm."
            )

        if residual is not None:
            if x.shape != residual.shape:
                raise ValueError(
                    f"x and residual shapes must match: {x.shape} vs {residual.shape}"
                )
            if x.dtype != residual.dtype:
                residual = residual.to(x.dtype)

        ctx.has_residual = residual is not None
        ctx.eps = eps
        ctx.orig_shape = orig_shape

        if x.numel() == 0:
            ctx.is_empty = True
            dummy_res = torch.empty_like(x) if residual is None else residual
            ctx.save_for_backward(x, dummy_res, gamma)
            out_res = torch.empty_like(x) if residual is None else (x + residual)
            return torch.empty_like(x), out_res

        ctx.is_empty = False
        x_flat = x.contiguous().view(-1, D)
        residual_flat = residual.contiguous().view(-1, D) if residual is not None else None
        gamma_flat = gamma.contiguous()
        M = x_flat.shape[0]

        use_triton = HAS_TRITON and x.is_cuda
        ctx.use_triton = use_triton

        if use_triton:
            y = torch.empty_like(x_flat)
            out_res = torch.empty_like(x_flat)
            rstd = torch.empty(M, device=x.device, dtype=torch.float32)
            BLOCK_SIZE = triton.next_power_of_2(D)
            num_warps = 4 if D <= 2048 else 8

            dummy_res = x_flat if residual_flat is None else residual_flat
            res_stride = 0 if residual_flat is None else dummy_res.stride(0)

            _fused_add_rmsnorm_fwd_kernel[(M,)](
                x_flat, dummy_res, y, out_res, gamma_flat, rstd,
                x_flat.stride(0), res_stride, y.stride(0), out_res.stride(0),
                D, eps,
                HAS_RESIDUAL=(residual is not None),
                BLOCK_SIZE=BLOCK_SIZE,
                num_warps=num_warps,
            )
            ctx.save_for_backward(out_res, gamma_flat, rstd)
            return y.view(orig_shape), out_res.view(orig_shape)
        else:
            x_fp32 = x_flat.float()
            if residual_flat is not None:
                r_fp32 = x_fp32 + residual_flat.float()
            else:
                r_fp32 = x_fp32
            rms = torch.sqrt(torch.mean(r_fp32 ** 2, dim=-1, keepdim=True) + eps)
            rstd = 1.0 / rms
            y = ((r_fp32 * rstd).to(gamma_flat.dtype) * gamma_flat).to(x.dtype)
            out_res = r_fp32.to(x.dtype)
            ctx.save_for_backward(out_res, gamma_flat)
            return y.view(orig_shape), out_res.view(orig_shape)

    @staticmethod
    def backward(ctx, dy: Tensor, dr_in: Optional[Tensor] = None) -> Tuple[Tensor, Optional[Tensor], Tensor, None]:
        if getattr(ctx, "is_empty", False) or dy.numel() == 0:
            if len(ctx.saved_tensors) >= 3:
                x_saved, res_saved, gamma_saved = ctx.saved_tensors
                dx = torch.zeros_like(x_saved)
                dres = torch.zeros_like(res_saved) if ctx.has_residual else None
                dgamma = torch.zeros_like(gamma_saved)
            else:
                dx = torch.zeros_like(dy)
                dres = torch.zeros_like(dy) if getattr(ctx, "has_residual", False) else None
                dgamma = torch.zeros(dy.shape[-1], dtype=dy.dtype, device=dy.device)
            return dx, dres, dgamma, None

        orig_shape = ctx.orig_shape
        D = orig_shape[-1]
        dy_flat = dy.contiguous().view(-1, D)
        M = dy_flat.shape[0]

        if ctx.use_triton:
            out_res, gamma_flat, rstd = ctx.saved_tensors
            dx = torch.empty_like(out_res)
            dres = torch.empty_like(out_res) if ctx.has_residual else None

            # Compact grouped dgamma buffer [num_programs, D]
            num_programs = min(128, M)
            rows_per_program = triton.cdiv(M, num_programs)
            partial_dw = torch.empty((num_programs, D), device=dy.device, dtype=torch.float32)

            BLOCK_SIZE = triton.next_power_of_2(D)
            num_warps = 4 if D <= 2048 else 8

            has_dr_in = dr_in is not None
            if has_dr_in:
                dr_in_flat = dr_in.contiguous().view(-1, D)
                dr_in_stride = dr_in_flat.stride(0)
            else:
                dr_in_flat = dy_flat  # dummy pointer, not accessed
                dr_in_stride = 0

            dres_arg = dres if ctx.has_residual else dx  # dummy pointer
            dres_stride = dres.stride(0) if ctx.has_residual else 0

            _fused_add_rmsnorm_bwd_kernel[(num_programs,)](
                dy_flat, dr_in_flat, out_res, gamma_flat, rstd, dx, dres_arg, partial_dw,
                dy_flat.stride(0), dr_in_stride, out_res.stride(0), dx.stride(0), dres_stride,
                M, D, rows_per_program,
                HAS_DR_IN=has_dr_in,
                HAS_DRES=ctx.has_residual,
                BLOCK_SIZE=BLOCK_SIZE,
                num_warps=num_warps,
            )
            dgamma = partial_dw.sum(dim=0).to(gamma_flat.dtype)
            dres_ret = dres.view(orig_shape) if ctx.has_residual else None
            return dx.view(orig_shape), dres_ret, dgamma, None
        else:
            out_res, gamma_flat = ctx.saved_tensors
            r_fp32 = out_res.float()
            dy_fp32 = dy_flat.float()
            g_fp32 = gamma_flat.float()

            rms = torch.sqrt(torch.mean(r_fp32 ** 2, dim=-1, keepdim=True) + ctx.eps)
            rstd = 1.0 / rms

            dy_g = dy_fp32 * g_fp32
            sum_dy_g_r = (dy_g * r_fp32).sum(dim=-1, keepdim=True)
            dr_norm = rstd * (dy_g - (rstd ** 2 / D) * r_fp32 * sum_dy_g_r)

            if dr_in is not None:
                dr_in_fp32 = dr_in.contiguous().view(-1, D).float()
                dr_total = dr_norm + dr_in_fp32
            else:
                dr_total = dr_norm

            dx = dr_total.to(dy.dtype).view(orig_shape)
            dres = dr_total.to(dy.dtype).view(orig_shape) if ctx.has_residual else None
            dgamma = (dy_fp32 * (r_fp32 * rstd)).sum(dim=0).to(gamma_flat.dtype)
            return dx, dres, dgamma, None


def fused_add_rmsnorm(
    x: Tensor,
    residual: Optional[Tensor],
    gamma: Tensor,
    eps: float = 1e-5,
) -> Tuple[Tensor, Tensor]:
    """Fused residual addition and RMSNorm.

    Computes:
        r = x + residual (or x if residual is None)
        y = RMSNorm(r, gamma, eps)

    Args:
        x: Input tensor [..., D]
        residual: Optional residual tensor to add [..., D]
        gamma: Learnable scale parameter [D]
        eps: Small constant for numerical stability

    Returns:
        Tuple of (y, updated_residual) where y is normalized output
        and updated_residual is x + residual (or x if residual is None).
    """
    if residual is not None and residual.dtype != x.dtype:
        residual = residual.to(x.dtype)
    return FusedAddRMSNormFunction.apply(x, residual, gamma, eps)


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization.

    Args:
        d_model: Input feature dimension
        eps: Small constant for numerical stability (default: 1e-5)
    """

    def __init__(self, d_model: int, eps: float = 1e-5) -> None:
        super().__init__()
        self.eps = eps
        self.gamma = nn.Parameter(torch.ones(d_model))

    def forward(self, x: Tensor) -> Tensor:
        """Apply RMSNorm.

        Args:
            x: Input tensor of shape (..., d_model)

        Returns:
            Normalized tensor of the same shape
        """
        return fused_rmsnorm(x, self.gamma, self.eps)

    def forward_add(self, x: Tensor, residual: Optional[Tensor] = None) -> Tuple[Tensor, Tensor]:
        """Apply fused residual addition + RMSNorm.

        Args:
            x: Input tensor of shape (..., d_model)
            residual: Optional residual tensor of shape (..., d_model)

        Returns:
            Tuple of (normalized_output, updated_residual)
        """
        return fused_add_rmsnorm(x, residual, self.gamma, self.eps)


__all__ = [
    "RMSNorm",
    "fused_rmsnorm",
    "fused_add_rmsnorm",
    "FusedRMSNormFunction",
    "FusedAddRMSNormFunction",
    "HAS_TRITON",
]
