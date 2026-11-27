"""M0.1 HPC GPU & Acceleration Kernel Package.

Provides high-performance operators, fused Triton kernels, and mathematical
orthogonalization routines optimized for AMD ROCm / RDNA 4 (Wave32 gfx1200) and NVIDIA CUDA:

- `rms_norm`: Triton RMSNorm forward/backward kernels and fused residual addition.
- `cross_entropy`: Fused chunked cross-entropy loss with online LogSumExp and zero-VRAM logit retention.
- `rope`: Fused Rotary Positional Embedding with zero activation caching and partial RoPE (p-RoPE).
- `swiglu`: Hardware-accelerated fused SwiGLU activation with register-level recomputation.
- `attention`: SDPA dispatching backend supporting Flash Attention (AOTriton), Efficient Attention, and Math fallback.
- `newton_schulz`: Quintic Newton-Schulz 5 zeropower orthogonalization for Muon optimizer.
"""

import os

# Ensure early AOTriton experimental kernels are enabled on AMD ROCm / RDNA 4 (gfx1200)
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

from .rms_norm import (
    RMSNorm,
    fused_rmsnorm,
    fused_add_rmsnorm,
    FusedRMSNormFunction,
    FusedAddRMSNormFunction,
)
from .cross_entropy import (
    fused_chunked_cross_entropy,
    FusedChunkedCrossEntropyFunction,
    FusedCrossEntropyLoss,
    _cross_entropy_fwd_bwd_kernel,
)
from .rope import (
    RotaryPositionalEmbedding,
    FusedRoPEFunction,
    fused_rope,
    _eager_rope_fwd,
    _eager_rope_bwd,
)
from .swiglu import (
    fused_swiglu,
    FusedSwiGLUFunction,
    BLOCK_SIZE,
    NUM_WARPS,
)
from .attention import (
    AttentionBackend,
    AttentionDispatcher,
)
from .newton_schulz import (
    zeropower_via_newtonschulz5,
)

__all__ = [
    # RMSNorm
    "RMSNorm",
    "fused_rmsnorm",
    "fused_add_rmsnorm",
    "FusedRMSNormFunction",
    "FusedAddRMSNormFunction",
    # Cross-Entropy
    "fused_chunked_cross_entropy",
    "FusedChunkedCrossEntropyFunction",
    "FusedCrossEntropyLoss",
    "_cross_entropy_fwd_bwd_kernel",
    # RoPE
    "RotaryPositionalEmbedding",
    "FusedRoPEFunction",
    "fused_rope",
    "_eager_rope_fwd",
    "_eager_rope_bwd",
    # SwiGLU
    "fused_swiglu",
    "FusedSwiGLUFunction",
    "BLOCK_SIZE",
    "NUM_WARPS",
    # Attention
    "AttentionBackend",
    "AttentionDispatcher",
    # Newton-Schulz
    "zeropower_via_newtonschulz5",
]
