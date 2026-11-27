"""Backend selection and safe fallback for scaled dot-product attention."""

from __future__ import annotations

import os

# Ensure early AOTriton experimental kernels are enabled on AMD ROCm / RDNA 4 (gfx1200)
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

from contextlib import nullcontext
from enum import Enum
import warnings

import torch
import torch.nn.functional as F


class AttentionBackend(str, Enum):
    AUTO = "auto"
    FLASH = "flash"
    EFFICIENT = "efficient"
    MATH = "math"


class AttentionDispatcher:
    """Dispatch SDPA to a preferred backend and fall back to math safely.

    Note on Sequence Packing & Explicit Attention Masks:
    Arbitrary 2D document attention masks (e.g. from PackedSequenceIterator) are
    supported by PyTorch SDPA under 'auto', 'efficient', and 'math' backends.
    Flash Attention (AOTriton/ROCm) does not support explicit attn_mask.
    If FLASH is preferred and an explicit attn_mask is supplied:
    - If allow_mask_fallback=False (default): raises ValueError to avoid unintended overhead.
    - If allow_mask_fallback=True: emits a RuntimeWarning and safely falls back to EFFICIENT/MATH.
    """

    def __init__(self, preferred_backend: str | AttentionBackend = AttentionBackend.AUTO) -> None:
        try:
            self.preferred_backend = AttentionBackend(preferred_backend)
        except ValueError as exc:
            choices = ", ".join(item.value for item in AttentionBackend)
            raise ValueError(f"Unknown attention backend {preferred_backend!r}; use {choices}") from exc
        self._warned = False

    def _context(self, backend: AttentionBackend):
        if backend is AttentionBackend.AUTO:
            return nullcontext()
        attention = getattr(torch.nn, "attention", None)
        if attention is None or not hasattr(attention, "sdpa_kernel"):
            return nullcontext()
        mapping = {
            AttentionBackend.FLASH: attention.SDPBackend.FLASH_ATTENTION,
            AttentionBackend.EFFICIENT: attention.SDPBackend.EFFICIENT_ATTENTION,
            AttentionBackend.MATH: attention.SDPBackend.MATH,
        }
        return attention.sdpa_kernel(mapping[backend])

    def dispatch(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        *,
        attn_mask: torch.Tensor | None = None,
        is_causal: bool = False,
        dropout_p: float = 0.0,
        allow_mask_fallback: bool = False,
    ) -> torch.Tensor:
        # Strict validation for FLASH backend to prevent silent fallback to MATH
        effective_backend = self.preferred_backend
        if self.preferred_backend == AttentionBackend.FLASH:
            if attn_mask is not None:
                if allow_mask_fallback:
                    if not self._warned:
                        warnings.warn(
                            "Flash Attention (AOTriton) does not support explicit dense attn_mask (e.g. packed sequences). "
                            "Falling back to EFFICIENT backend because allow_mask_fallback=True.",
                            RuntimeWarning,
                            stacklevel=2,
                        )
                        self._warned = True
                    effective_backend = AttentionBackend.EFFICIENT if q.is_cuda else AttentionBackend.MATH
                else:
                    raise ValueError(
                        "Flash Attention (AOTriton) on ROCm does not support explicit attn_mask. "
                        "Use is_causal=True and attn_mask=None to satisfy AOTriton requirements without falling back to MATH. "
                        "For packed sequences with 2D document masks, use AttentionBackend.EFFICIENT, MATH, or AUTO, "
                        "or pass allow_mask_fallback=True."
                    )
            elif not q.is_cuda:
                raise RuntimeError(
                    f"Flash Attention (AOTriton) requires a CUDA/ROCm GPU device, but inputs are on {q.device}."
                )
            elif q.dtype not in (torch.float16, torch.bfloat16):
                raise ValueError(
                    f"Flash Attention (AOTriton) requires half-precision (torch.float16 or torch.bfloat16) on ROCm, "
                    f"but got query dtype {q.dtype}. Disallowing silent fallback to MATH."
                )

        kwargs = {
            "attn_mask": attn_mask,
            "dropout_p": dropout_p,
            "is_causal": is_causal,
        }
        try:
            with self._context(effective_backend):
                return F.scaled_dot_product_attention(q, k, v, **kwargs)
        except RuntimeError as exc:
            if effective_backend in (AttentionBackend.AUTO, AttentionBackend.MATH, AttentionBackend.FLASH):
                raise
            if not self._warned:
                warnings.warn(
                    f"SDPA backend {effective_backend.value!r} failed; falling back to math: {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                self._warned = True
            with self._context(AttentionBackend.MATH):
                return F.scaled_dot_product_attention(q, k, v, **kwargs)


__all__ = [
    "AttentionBackend",
    "AttentionDispatcher",
]
