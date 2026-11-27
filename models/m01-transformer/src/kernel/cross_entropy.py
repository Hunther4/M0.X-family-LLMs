"""Fused Chunked Cross-Entropy Loss with Triton and PyTorch Autograd Integration.

Optimized for AMD ROCm / RDNA 4 (gfx1200) and CUDA architectures.
Eliminates full-vocabulary logit tensor materialization in VRAM by chunking
tokens along the sequence dimension, computing projections chunk-by-chunk,
and using a fused Triton kernel with online LogSumExp and in-place analytical
gradient backpropagation.
"""

from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
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
    def _cross_entropy_fwd_bwd_kernel(
        LOGITS_ptr,
        TARGETS_ptr,
        LOSSES_ptr,
        stride_logits_row: tl.int64,
        stride_logits_col: tl.int64,
        V: tl.int64,
        n_valid: tl.float32,
        ignore_index: tl.int64,
        BLOCK_V: tl.constexpr,
        COMPUTE_BWD: tl.constexpr = True,
    ):
        """Fused Cross-Entropy Forward and Backward Kernel.

        Each program instance processes one token row i of the logits chunk.
        Pass 1: Numerically stable online LogSumExp reduction across vocabulary tiles.
        Pass 2: In-place overwrite of logits with analytical gradient:
                grad_ij = (1 / N_valid) * (p_ij - 1(j == target_i))
        """
        row_idx = tl.program_id(0).to(tl.int64)
        target = tl.load(TARGETS_ptr + row_idx).to(tl.int64)
        row_logits_ptr = LOGITS_ptr + row_idx * stride_logits_row

        # Handle ignored or invalid targets
        if (target == ignore_index) or (target < 0) or (target >= V):
            tl.store(LOSSES_ptr + row_idx, 0.0)
            if COMPUTE_BWD:
                zero = 0.0
                for start_v in range(0, V, BLOCK_V):
                    cols = start_v + tl.arange(0, BLOCK_V)
                    mask = cols < V
                    tl.store(
                        row_logits_ptr + cols * stride_logits_col,
                        zero.to(LOGITS_ptr.dtype.element_ty),
                        mask=mask,
                    )
            return

        inv_n_valid = 1.0 / n_valid if n_valid > 0.0 else 0.0
        target_logit = tl.load(row_logits_ptr + target * stride_logits_col).to(tl.float32)

        # ── Pass 1: Numerically Stable Online LogSumExp (FP32) ────────────────
        m_val = -1e30
        d_val = 0.0

        for start_v in range(0, V, BLOCK_V):
            cols = start_v + tl.arange(0, BLOCK_V)
            mask = cols < V
            x = tl.load(
                row_logits_ptr + cols * stride_logits_col,
                mask=mask,
                other=-1e30,
            ).to(tl.float32)

            m_block = tl.max(tl.where(mask, x, -1e30), axis=0)
            m_new = tl.maximum(m_val, m_block)

            # Online denominator update: d_new = d_old * exp(m_old - m_new) + sum(exp(x - m_new))
            exp_term = tl.where(mask, tl.exp(x - m_new), 0.0)
            d_val = d_val * tl.exp(m_val - m_new) + tl.sum(exp_term, axis=0)
            m_val = m_new

        lse = m_val + tl.log(d_val)
        loss = (lse - target_logit) * inv_n_valid
        tl.store(LOSSES_ptr + row_idx, loss)

        # ── Pass 2: In-place Overwrite with Analytical Gradient ───────────────
        if COMPUTE_BWD:
            for start_v in range(0, V, BLOCK_V):
                cols = start_v + tl.arange(0, BLOCK_V)
                mask = cols < V
                x = tl.load(
                    row_logits_ptr + cols * stride_logits_col,
                    mask=mask,
                    other=0.0,
                ).to(tl.float32)

                p = tl.exp(x - m_val) / d_val
                is_target = (cols == target).to(tl.float32)
                grad = (p - is_target) * inv_n_valid

                tl.store(
                    row_logits_ptr + cols * stride_logits_col,
                    grad.to(LOGITS_ptr.dtype.element_ty),
                    mask=mask,
                )
else:
    _cross_entropy_fwd_bwd_kernel = None


def _chunked_cross_entropy_pytorch(
    hidden_states: Tensor,
    weight: Tensor,
    targets: Tensor,
    ignore_index: int = -100,
    chunk_size: int = 2048,
    reduction: str = "mean",
) -> Tensor:
    """Pure PyTorch fallback for chunked cross-entropy (CPU or non-Triton)."""
    orig_shape = hidden_states.shape
    H = hidden_states.view(-1, orig_shape[-1])
    Y = targets.view(-1)
    N = H.shape[0]
    V = weight.shape[0]

    valid_mask = (Y != ignore_index) & (Y >= 0) & (Y < V)
    n_valid = valid_mask.sum().float()

    if n_valid.item() == 0:
        loss = H.sum() * 0.0
        if weight is not None and weight.requires_grad:
            loss = loss + weight.sum() * 0.0
        return loss.to(hidden_states.dtype)

    losses = []
    for start_idx in range(0, N, chunk_size):
        end_idx = min(start_idx + chunk_size, N)
        H_c = H[start_idx:end_idx]
        Y_c = Y[start_idx:end_idx]

        # Filter out-of-bounds targets to ignore_index for F.cross_entropy safety
        if ((Y_c < 0) | (Y_c >= V)).any():
            Y_c = Y_c.clone()
            Y_c[(Y_c < 0) | (Y_c >= V)] = ignore_index

        logits_c = torch.matmul(H_c, weight.t())
        loss_c = F.cross_entropy(
            logits_c, Y_c, ignore_index=ignore_index, reduction="sum"
        )
        losses.append(loss_c)

    total_loss = sum(losses)

    if reduction == "mean":
        return total_loss / n_valid
    elif reduction == "sum":
        return total_loss
    else:
        raise ValueError(f"Unsupported reduction for chunked loss: {reduction}")


class FusedChunkedCrossEntropyFunction(torch.autograd.Function):
    """Autograd Function for Chunked Fused Cross-Entropy with Triton.

    Iterates over token hidden states in chunks of size C (e.g. 2048),
    projects each chunk H_chunk @ W.T to logits, calculates loss, and
    analytically backpropagates to H_chunk and W without ever retaining
    the full (N, V) logits in VRAM.
    """

    @staticmethod
    def forward(
        ctx,
        hidden_states: Tensor,
        weight: Tensor,
        targets: Tensor,
        ignore_index: int = -100,
        chunk_size: int = 2048,
        block_v: int = 1024,
    ) -> Tensor:
        orig_shape = hidden_states.shape
        H = hidden_states.view(-1, orig_shape[-1]).contiguous()
        W = weight.contiguous()
        Y = targets.view(-1).contiguous()
        N, D = H.shape
        V = W.shape[0]

        valid_mask = (Y != ignore_index) & (Y >= 0) & (Y < V)
        n_valid = valid_mask.sum().item()
        n_valid_f = float(n_valid)

        req_grad_H = ctx.needs_input_grad[0]
        req_grad_W = ctx.needs_input_grad[1]
        compute_bwd = req_grad_H or req_grad_W

        grad_H = torch.empty_like(H) if req_grad_H else None
        # Accumulate grad_W in float32 (Liger-Kernel style) to prevent precision loss across many chunks
        grad_W_accum = torch.zeros((V, D), device=W.device, dtype=torch.float32) if req_grad_W else None

        total_loss = torch.zeros((), device=H.device, dtype=torch.float32)

        # Configure BLOCK_V power of 2, minimum 16
        actual_block_v = max(16, triton.next_power_of_2(min(block_v, V)))

        if n_valid == 0:
            ctx.grad_H = torch.zeros_like(H).view(orig_shape) if req_grad_H else None
            ctx.grad_W = torch.zeros_like(W) if req_grad_W else None
            return total_loss.to(hidden_states.dtype)

        for start_idx in range(0, N, chunk_size):
            end_idx = min(start_idx + chunk_size, N)
            M = end_idx - start_idx

            H_chunk = H[start_idx:end_idx]
            Y_chunk = Y[start_idx:end_idx]

            # Project H_chunk @ W.T: (M, D) x (D, V) -> (M, V)
            logits_chunk = torch.matmul(H_chunk, W.t())

            losses_chunk = torch.empty(M, device=H.device, dtype=torch.float32)

            _cross_entropy_fwd_bwd_kernel[(M,)](
                logits_chunk,
                Y_chunk,
                losses_chunk,
                logits_chunk.stride(0),
                logits_chunk.stride(1),
                V,
                n_valid_f,
                ignore_index,
                BLOCK_V=actual_block_v,
                COMPUTE_BWD=compute_bwd,
            )

            total_loss = total_loss + losses_chunk.sum()

            if req_grad_H:
                # logits_chunk is now overwritten in-place with d(Loss)/d(logits_chunk)
                grad_H[start_idx:end_idx] = torch.matmul(logits_chunk, W)

            if req_grad_W:
                grad_W_accum.addmm_(logits_chunk.float().t(), H_chunk.float())

        ctx.grad_H = grad_H.view(orig_shape) if req_grad_H else None
        ctx.grad_W = grad_W_accum.to(W.dtype) if req_grad_W else None

        return total_loss.to(hidden_states.dtype)

    @staticmethod
    def backward(ctx, grad_output: Tensor) -> Tuple[Optional[Tensor], Optional[Tensor], None, None, None, None]:
        grad_H = ctx.grad_H
        grad_W = ctx.grad_W

        if grad_output.item() != 1.0:
            scale = grad_output.to(grad_H.dtype if grad_H is not None else (grad_W.dtype if grad_W is not None else torch.float32))
            if grad_H is not None:
                grad_H = grad_H * scale
            if grad_W is not None:
                grad_W = grad_W * scale

        return grad_H, grad_W, None, None, None, None


def fused_chunked_cross_entropy(
    hidden_states: Tensor,
    weight: Tensor,
    targets: Tensor,
    ignore_index: int = -100,
    chunk_size: int = 2048,
    reduction: str = "mean",
    block_v: int = 1024,
) -> Tensor:
    """Compute fused chunked cross-entropy loss without global logit materialization.

    Args:
        hidden_states: Hidden representations of shape (batch, seq_len, d_model) or (N, d_model).
        weight: Tied embedding / LM head projection weight of shape (vocab_size, d_model).
        targets: Ground-truth target token IDs of shape (batch, seq_len) or (N,).
        ignore_index: Token index to ignore in loss and gradients (default -100).
        chunk_size: Number of tokens per chunk C to process sequentially (default 2048).
        reduction: Reduction method ('mean' or 'sum'). Default 'mean'.
        block_v: Triton vocabulary tiling block size (default 1024).

    Returns:
        Scalar loss tensor normalized by the number of valid tokens.
    """
    if reduction not in ("mean", "sum"):
        raise ValueError(f"fused_chunked_cross_entropy supports reduction='mean' or 'sum', got {reduction}")

    if hidden_states.is_cuda and HAS_TRITON:
        V = weight.shape[0]
        valid_mask = (targets.view(-1) != ignore_index) & (targets.view(-1) >= 0) & (targets.view(-1) < V)
        n_valid = valid_mask.sum().float()

        if n_valid.item() == 0:
            loss = hidden_states.sum() * 0.0
            if weight.requires_grad:
                loss = loss + weight.sum() * 0.0
            return loss.to(hidden_states.dtype)

        if reduction == "mean":
            return FusedChunkedCrossEntropyFunction.apply(
                hidden_states, weight, targets, ignore_index, chunk_size, block_v
            )
        else:
            # reduction == 'sum': set ignore_index and sum scale
            loss = FusedChunkedCrossEntropyFunction.apply(
                hidden_states, weight, targets, ignore_index, chunk_size, block_v
            )
            return loss * n_valid

    return _chunked_cross_entropy_pytorch(
        hidden_states,
        weight,
        targets,
        ignore_index=ignore_index,
        chunk_size=chunk_size,
        reduction=reduction,
    )


class FusedCrossEntropyLoss(nn.Module):
    """Fused Chunked Cross-Entropy Loss module.

    Wraps `fused_chunked_cross_entropy` into a PyTorch nn.Module for use
    in training pipelines and loss managers.

    Args:
        ignore_index: Token ID to ignore in loss calculation (default: -100).
        chunk_size: Chunk size along sequence/token dimension (default: 2048).
        reduction: 'mean' or 'sum' reduction (default: 'mean').
        block_v: Triton block size for vocabulary tiling (default: 1024).
    """

    def __init__(
        self,
        weight: Optional[Tensor] = None,
        ignore_index: int = -100,
        chunk_size: int = 2048,
        reduction: str = "mean",
        block_v: int = 1024,
    ) -> None:
        super().__init__()
        self.embedding_weight = weight
        self.ignore_index = ignore_index
        self.chunk_size = chunk_size
        self.reduction = reduction
        self.block_v = block_v

    def forward(
        self,
        hidden_states: Tensor,
        targets_or_weight: Tensor,
        targets: Optional[Tensor] = None,
    ) -> Tensor:
        """Calculate fused chunked cross entropy.

        Usage:
            loss = criterion(hidden_states, weight, targets)
            # OR (if weight was provided during __init__):
            loss = criterion(hidden_states, targets)
        """
        if targets is None:
            # Called as criterion(hidden_states, targets) with self.embedding_weight
            if self.embedding_weight is None:
                raise ValueError(
                    "FusedCrossEntropyLoss requires weight passed either to __init__ "
                    "or as the second argument: criterion(hidden_states, weight, targets)"
                )
            weight = self.embedding_weight
            target_tensor = targets_or_weight
        else:
            # Called as criterion(hidden_states, weight, targets)
            weight = targets_or_weight
            target_tensor = targets

        return fused_chunked_cross_entropy(
            hidden_states=hidden_states,
            weight=weight,
            targets=target_tensor,
            ignore_index=self.ignore_index,
            chunk_size=self.chunk_size,
            reduction=self.reduction,
            block_v=self.block_v,
        )


__all__ = [
    "fused_chunked_cross_entropy",
    "FusedChunkedCrossEntropyFunction",
    "FusedCrossEntropyLoss",
    "_cross_entropy_fwd_bwd_kernel",
    "_chunked_cross_entropy_pytorch",
    "HAS_TRITON",
]
