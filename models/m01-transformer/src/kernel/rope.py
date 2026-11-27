"""Rotary Positional Embedding (RoPE) with Triton and PyTorch Autograd Integration.

Optimized for AMD ROCm / RDNA 4 (gfx1200) and CUDA architectures.
Supports full RoPE and partial RoPE (p-RoPE) for improved long-context extrapolation.

Reference: https://arxiv.org/abs/2104.09864 (RoFormer: Enhanced Transformer with Rotary Position Embedding)
Partial RoPE (p-RoPE): https://arxiv.org/abs/2410.06205 / https://arxiv.org/abs/2501.18795
Gemma 4 Technical Report: https://arxiv.org/abs/2607.02770

Math:
    θᵢ = 1 / rope_theta^(2i/d_head) for i ∈ [0, rotary_dim/2)
    Position m rotation (full RoPE):
        rotated_even = x_even·cos(mθ) - x_odd·sin(mθ)
        rotated_odd  = x_even·sin(mθ) + x_odd·cos(mθ)
    p-RoPE: only apply to first rotary_dim dimensions, remaining dimensions pass through.

Analytical Gradient (Zero VRAM Activations):
    Since R(θ)^T = R(-θ), the analytical backward gradient is the rotation of dy with -sin:
        dx_even = dy_even·cos(mθ) + dy_odd·sin(mθ)
        dx_odd  = -dy_even·sin(mθ) + dy_odd·cos(mθ)
    Pass-through dimensions copy directly: dx_pass = dy_pass.
    Crucially, the input tensor `x` is NOT saved for backward in autograd, achieving
    100% RoPE activation memory savings in VRAM during training.
"""

import math
from typing import Any, Optional, Tuple, Union, TYPE_CHECKING
import torch
import torch.nn as nn

if TYPE_CHECKING:
    from src.transformer.config import M01Config

try:
    import triton
    import triton.language as tl
    HAS_TRITON = True
except ImportError:
    triton = None
    tl = None
    HAS_TRITON = False


# =====================================================================
# Triton GPU Kernels (Optimized for RDNA 4 gfx1200 & CUDA)
# =====================================================================

if HAS_TRITON:
    @triton.jit
    def _rope_fwd_kernel(
        X_ptr,
        OUT_ptr,
        FREQS_ptr,
        stride_x_b: tl.int64,
        stride_x_s: tl.int64,
        stride_x_h: tl.int64,
        stride_x_d: tl.int64,
        stride_out_b: tl.int64,
        stride_out_s: tl.int64,
        stride_out_h: tl.int64,
        stride_out_d: tl.int64,
        batch: tl.int64,
        seq_len: tl.int64,
        n_heads: tl.int64,
        d_head: tl.int64,
        rotary_dim: tl.int64,
        OFFSET_OR_VAL,
        IS_OFFSET_TENSOR: tl.constexpr,
        HAS_PASS: tl.constexpr,
        BLOCK_ROT: tl.constexpr,
        BLOCK_PASS: tl.constexpr,
    ):
        """Fused RoPE forward kernel.

        Processes (batch, seq_len, n_heads, d_head) tensors.
        Applies in-register coordinate rotation to even/odd pairs up to rotary_dim,
        and directly copies any remaining dimensions beyond rotary_dim (p-RoPE).
        """
        pid = tl.program_id(0).to(tl.int64)

        head_idx = pid % n_heads
        token_idx = pid // n_heads
        seq_idx = token_idx % seq_len
        batch_idx = token_idx // seq_len

        if IS_OFFSET_TENSOR:
            off = tl.load(OFFSET_OR_VAL).to(tl.int64)
        else:
            off = OFFSET_OR_VAL

        pos = (off + seq_idx).to(tl.float32)

        row_x_ptr = X_ptr + batch_idx * stride_x_b + seq_idx * stride_x_s + head_idx * stride_x_h
        row_out_ptr = OUT_ptr + batch_idx * stride_out_b + seq_idx * stride_out_s + head_idx * stride_out_h

        half_rot = rotary_dim // 2
        cols = tl.arange(0, BLOCK_ROT)
        mask = cols < half_rot

        idx_even = 2 * cols
        idx_odd = 2 * cols + 1

        x_even = tl.load(row_x_ptr + idx_even * stride_x_d, mask=mask, other=0.0).to(tl.float32)
        x_odd  = tl.load(row_x_ptr + idx_odd * stride_x_d, mask=mask, other=0.0).to(tl.float32)
        freq   = tl.load(FREQS_ptr + cols, mask=mask, other=0.0).to(tl.float32)

        angle = pos * freq
        cos_val = tl.cos(angle)
        sin_val = tl.sin(angle)

        rot_even = x_even * cos_val - x_odd * sin_val
        rot_odd  = x_even * sin_val + x_odd * cos_val

        tl.store(row_out_ptr + idx_even * stride_out_d, rot_even.to(OUT_ptr.dtype.element_ty), mask=mask)
        tl.store(row_out_ptr + idx_odd * stride_out_d, rot_odd.to(OUT_ptr.dtype.element_ty), mask=mask)

        if HAS_PASS:
            pass_dim = d_head - rotary_dim
            pass_cols = tl.arange(0, BLOCK_PASS)
            pass_mask = pass_cols < pass_dim
            x_pass = tl.load(row_x_ptr + (rotary_dim + pass_cols) * stride_x_d, mask=pass_mask, other=0.0)
            tl.store(row_out_ptr + (rotary_dim + pass_cols) * stride_out_d, x_pass, mask=pass_mask)

    @triton.jit
    def _rope_bwd_kernel(
        DY_ptr,
        DX_ptr,
        FREQS_ptr,
        stride_dy_b: tl.int64,
        stride_dy_s: tl.int64,
        stride_dy_h: tl.int64,
        stride_dy_d: tl.int64,
        stride_dx_b: tl.int64,
        stride_dx_s: tl.int64,
        stride_dx_h: tl.int64,
        stride_dx_d: tl.int64,
        batch: tl.int64,
        seq_len: tl.int64,
        n_heads: tl.int64,
        d_head: tl.int64,
        rotary_dim: tl.int64,
        OFFSET_OR_VAL,
        IS_OFFSET_TENSOR: tl.constexpr,
        HAS_PASS: tl.constexpr,
        BLOCK_ROT: tl.constexpr,
        BLOCK_PASS: tl.constexpr,
    ):
        """Fused RoPE backward kernel.

        Given R(θ)^T = R(-θ), computes analytical gradients:
            dx_even = dy_even * cos + dy_odd * sin
            dx_odd  = -dy_even * sin + dy_odd * cos
        Does not require input activation x!
        """
        pid = tl.program_id(0).to(tl.int64)

        head_idx = pid % n_heads
        token_idx = pid // n_heads
        seq_idx = token_idx % seq_len
        batch_idx = token_idx // seq_len

        if IS_OFFSET_TENSOR:
            off = tl.load(OFFSET_OR_VAL).to(tl.int64)
        else:
            off = OFFSET_OR_VAL

        pos = (off + seq_idx).to(tl.float32)

        row_dy_ptr = DY_ptr + batch_idx * stride_dy_b + seq_idx * stride_dy_s + head_idx * stride_dy_h
        row_dx_ptr = DX_ptr + batch_idx * stride_dx_b + seq_idx * stride_dx_s + head_idx * stride_dx_h

        half_rot = rotary_dim // 2
        cols = tl.arange(0, BLOCK_ROT)
        mask = cols < half_rot

        idx_even = 2 * cols
        idx_odd = 2 * cols + 1

        dy_even = tl.load(row_dy_ptr + idx_even * stride_dy_d, mask=mask, other=0.0).to(tl.float32)
        dy_odd  = tl.load(row_dy_ptr + idx_odd * stride_dy_d, mask=mask, other=0.0).to(tl.float32)
        freq    = tl.load(FREQS_ptr + cols, mask=mask, other=0.0).to(tl.float32)

        angle = pos * freq
        cos_val = tl.cos(angle)
        sin_val = tl.sin(angle)

        dx_even = dy_even * cos_val + dy_odd * sin_val
        dx_odd  = -dy_even * sin_val + dy_odd * cos_val

        tl.store(row_dx_ptr + idx_even * stride_dx_d, dx_even.to(DX_ptr.dtype.element_ty), mask=mask)
        tl.store(row_dx_ptr + idx_odd * stride_dx_d, dx_odd.to(DX_ptr.dtype.element_ty), mask=mask)

        if HAS_PASS:
            pass_dim = d_head - rotary_dim
            pass_cols = tl.arange(0, BLOCK_PASS)
            pass_mask = pass_cols < pass_dim
            dy_pass = tl.load(row_dy_ptr + (rotary_dim + pass_cols) * stride_dy_d, mask=pass_mask, other=0.0)
            tl.store(row_dx_ptr + (rotary_dim + pass_cols) * stride_dx_d, dy_pass, mask=pass_mask)


# =====================================================================
# Eager PyTorch Fallbacks (CPU & Pure PyTorch Reference)
# =====================================================================

def _eager_rope_fwd(
    x: torch.Tensor,
    freqs: torch.Tensor,
    offset: Union[int, torch.Tensor],
    rotary_dim: int,
) -> torch.Tensor:
    """CPU/Eager forward pass for Rotary Positional Embedding."""
    batch, seq_len, n_heads, d_head = x.shape
    x_rot = x[..., :rotary_dim]
    x_pass = x[..., rotary_dim:]

    if isinstance(offset, torch.Tensor):
        positions = torch.arange(0, seq_len, device=x.device, dtype=torch.float32) + offset.to(device=x.device, dtype=torch.float32)
    else:
        positions = torch.arange(offset, offset + seq_len, device=x.device, dtype=torch.float32)

    freqs_sliced = freqs[:rotary_dim // 2].float()
    angles = positions.unsqueeze(1) * freqs_sliced.unsqueeze(0)

    cos = torch.cos(angles).to(x.dtype).unsqueeze(0).unsqueeze(2)
    sin = torch.sin(angles).to(x.dtype).unsqueeze(0).unsqueeze(2)

    x_even = x_rot[..., 0::2]
    x_odd = x_rot[..., 1::2]

    rot_even = x_even * cos - x_odd * sin
    rot_odd  = x_even * sin + x_odd * cos

    rotated = torch.stack([rot_even, rot_odd], dim=-1).reshape(batch, seq_len, n_heads, rotary_dim)
    if x_pass.shape[-1] == 0:
        return rotated
    return torch.cat([rotated, x_pass], dim=-1)


def _eager_rope_bwd(
    dy: torch.Tensor,
    freqs: torch.Tensor,
    offset: Union[int, torch.Tensor],
    rotary_dim: int,
) -> torch.Tensor:
    """CPU/Eager analytical backward pass for Rotary Positional Embedding."""
    batch, seq_len, n_heads, d_head = dy.shape
    dy_rot = dy[..., :rotary_dim]
    dy_pass = dy[..., rotary_dim:]

    if isinstance(offset, torch.Tensor):
        positions = torch.arange(0, seq_len, device=dy.device, dtype=torch.float32) + offset.to(device=dy.device, dtype=torch.float32)
    else:
        positions = torch.arange(offset, offset + seq_len, device=dy.device, dtype=torch.float32)

    freqs_sliced = freqs[:rotary_dim // 2].float()
    angles = positions.unsqueeze(1) * freqs_sliced.unsqueeze(0)

    cos = torch.cos(angles).to(dy.dtype).unsqueeze(0).unsqueeze(2)
    sin = torch.sin(angles).to(dy.dtype).unsqueeze(0).unsqueeze(2)

    dy_even = dy_rot[..., 0::2]
    dy_odd = dy_rot[..., 1::2]

    dx_even = dy_even * cos + dy_odd * sin
    dx_odd  = -dy_even * sin + dy_odd * cos

    dx_rot = torch.stack([dx_even, dx_odd], dim=-1).reshape(batch, seq_len, n_heads, rotary_dim)
    if dy_pass.shape[-1] == 0:
        return dx_rot
    return torch.cat([dx_rot, dy_pass], dim=-1)


# =====================================================================
# Autograd Function Wrapper
# =====================================================================

class FusedRoPEFunction(torch.autograd.Function):
    """PyTorch autograd Function for Fused RoPE.

    Saves ONLY `freqs` (and optional offset tensor) in `ctx.save_for_backward`.
    Activations `x` are NOT saved, providing 100% RoPE activation VRAM savings.
    """

    @staticmethod
    def forward(
        ctx,
        x: torch.Tensor,
        freqs: torch.Tensor,
        offset: Union[int, torch.Tensor] = 0,
        rotary_dim: Optional[int] = None,
    ) -> torch.Tensor:
        is_offset_tensor = isinstance(offset, torch.Tensor)
        if is_offset_tensor:
            if x.is_cuda and not offset.is_cuda:
                offset_arg = offset.to(device=x.device, dtype=torch.int64)
            elif not x.is_cuda and offset.is_cuda:
                offset_arg = offset.to(device=x.device, dtype=torch.int64)
            else:
                offset_arg = offset.to(dtype=torch.int64)
            ctx.offset_is_tensor = True
            ctx.save_for_backward(freqs, offset_arg)
        else:
            offset_val = int(offset)
            offset_arg = offset_val
            ctx.offset_is_tensor = False
            ctx.offset_val = offset_val
            ctx.save_for_backward(freqs)

        if rotary_dim is None:
            rotary_dim_val = freqs.shape[0] * 2
        else:
            rotary_dim_val = int(rotary_dim)

        rotary_dim_val = min(rotary_dim_val, x.shape[-1])
        if rotary_dim_val % 2 != 0:
            rotary_dim_val -= 1
        rotary_dim_val = max(2, rotary_dim_val)

        ctx.rotary_dim = rotary_dim_val

        # Handle 3D inputs (e.g. [seq_len, n_heads, d_head] or [batch, seq_len, d_head])
        is_3d = False
        if x.dim() == 3:
            is_3d = True
            x = x.unsqueeze(0)

        # Clean fallback for CPU execution or when Triton is unavailable
        if not HAS_TRITON or not x.is_cuda:
            out = _eager_rope_fwd(x, freqs, offset_arg, rotary_dim_val)
            return out.squeeze(0) if is_3d else out

        batch, seq_len, n_heads, d_head = x.shape
        if batch == 0 or seq_len == 0:
            out = torch.empty_like(x)
            return out.squeeze(0) if is_3d else out

        x_contig = x if x.is_contiguous() else x.contiguous()
        freqs_contig = freqs if freqs.is_contiguous() else freqs.contiguous()
        out = torch.empty_like(x_contig)

        has_pass = rotary_dim_val < d_head
        half_rot = rotary_dim_val // 2
        block_rot = max(32, triton.next_power_of_2(half_rot))
        block_pass = max(32, triton.next_power_of_2(d_head - rotary_dim_val)) if has_pass else 32

        grid = (batch * seq_len * n_heads,)
        _rope_fwd_kernel[grid](
            x_contig,
            out,
            freqs_contig,
            x_contig.stride(0),
            x_contig.stride(1),
            x_contig.stride(2),
            x_contig.stride(3),
            out.stride(0),
            out.stride(1),
            out.stride(2),
            out.stride(3),
            batch,
            seq_len,
            n_heads,
            d_head,
            rotary_dim_val,
            offset_arg,
            IS_OFFSET_TENSOR=is_offset_tensor,
            HAS_PASS=has_pass,
            BLOCK_ROT=block_rot,
            BLOCK_PASS=block_pass,
        )

        return out.squeeze(0) if is_3d else out

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor):
        if ctx.offset_is_tensor:
            freqs, offset_arg = ctx.saved_tensors
            is_offset_tensor = True
        else:
            (freqs,) = ctx.saved_tensors
            offset_arg = ctx.offset_val
            is_offset_tensor = False

        rotary_dim_val = ctx.rotary_dim

        is_3d = False
        if grad_output.dim() == 3:
            is_3d = True
            grad_output = grad_output.unsqueeze(0)

        if not HAS_TRITON or not grad_output.is_cuda:
            dx = _eager_rope_bwd(grad_output, freqs, offset_arg, rotary_dim_val)
            dx = dx.squeeze(0) if is_3d else dx
            return dx, None, None, None

        batch, seq_len, n_heads, d_head = grad_output.shape
        if batch == 0 or seq_len == 0:
            dx = torch.empty_like(grad_output)
            return dx.squeeze(0) if is_3d else dx, None, None, None

        dy_contig = grad_output if grad_output.is_contiguous() else grad_output.contiguous()
        freqs_contig = freqs if freqs.is_contiguous() else freqs.contiguous()
        dx = torch.empty_like(dy_contig)

        has_pass = rotary_dim_val < d_head
        half_rot = rotary_dim_val // 2
        block_rot = max(32, triton.next_power_of_2(half_rot))
        block_pass = max(32, triton.next_power_of_2(d_head - rotary_dim_val)) if has_pass else 32

        grid = (batch * seq_len * n_heads,)
        _rope_bwd_kernel[grid](
            dy_contig,
            dx,
            freqs_contig,
            dy_contig.stride(0),
            dy_contig.stride(1),
            dy_contig.stride(2),
            dy_contig.stride(3),
            dx.stride(0),
            dx.stride(1),
            dx.stride(2),
            dx.stride(3),
            batch,
            seq_len,
            n_heads,
            d_head,
            rotary_dim_val,
            offset_arg,
            IS_OFFSET_TENSOR=is_offset_tensor,
            HAS_PASS=has_pass,
            BLOCK_ROT=block_rot,
            BLOCK_PASS=block_pass,
        )

        dx = dx.squeeze(0) if is_3d else dx
        return dx, None, None, None


def fused_rope(
    x: torch.Tensor,
    freqs: torch.Tensor,
    offset: Union[int, torch.Tensor] = 0,
    rotary_dim: Optional[int] = None,
) -> torch.Tensor:
    """Apply fused rotary positional embedding using Triton on GPU or eager fallback on CPU."""
    return FusedRoPEFunction.apply(x, freqs, offset, rotary_dim)


# =====================================================================
# Rotary Positional Embedding Module
# =====================================================================

class RotaryPositionalEmbedding(nn.Module):
    """Rotary Positional Embedding using explicit sin/cos rotation with Triton acceleration.

    Supports partial rotation (p-RoPE) where only a fraction of head dimensions
    carry positional information, leaving the rest position-free for semantic capacity.
    """

    def __init__(self, config: Union["M01Config", Any]) -> None:
        """Initialize RoPE with precomputed inverse frequencies.

        Args:
            config: M01Config with d_head, rope_theta, and optional partial_rotary_factor
        """
        super().__init__()

        d_head = config.d_head
        self.partial_rotary_factor = getattr(config, 'partial_rotary_factor', 1.0)

        # Compute the number of dimensions to rotate (must be even)
        self.rotary_dim = int(d_head * self.partial_rotary_factor)
        if self.rotary_dim % 2 != 0:
            self.rotary_dim -= 1  # Round down to even
        self.rotary_dim = max(2, self.rotary_dim)  # At least 2 dimensions

        # Compute inverse frequencies for rotated dimensions only
        # θᵢ = 1 / rope_theta^(2i/d_head) for i ∈ [0, rotary_dim/2)
        freqs = 1.0 / (config.rope_theta ** (torch.arange(0, self.rotary_dim, 2).float() / d_head))

        # Store as buffer (part of module state, moved across devices with module)
        self.register_buffer("freqs", freqs)

    def forward(self, x: torch.Tensor, offset: Union[int, torch.Tensor] = 0) -> torch.Tensor:
        """Apply rotary positional embedding to input tensor.

        Args:
            x: Input tensor of shape (batch, seq_len, n_heads, d_head)
            offset: Starting position offset (for cached autoregressive generation)

        Returns:
            Rotated tensor of same shape
        """
        return FusedRoPEFunction.apply(x, self.freqs, offset, self.rotary_dim)


__all__ = [
    "RotaryPositionalEmbedding",
    "FusedRoPEFunction",
    "fused_rope",
    "_eager_rope_fwd",
    "_eager_rope_bwd",
    "HAS_TRITON",
]
