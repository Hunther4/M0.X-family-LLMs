"""Canonical Newton-Schulz 5 Zeropower Orthogonalization Kernel.

Computes the nearest orthogonal matrix (zeroth power) of a matrix or batch of matrices
using quintic Newton-Schulz iterations:
    X_{k+1} = a * X_k + (b * A_k + c * A_k^2) * X_k
    where A_k = X_k @ X_k^T, and coefficients (a, b, c) = (3.4445, -4.7750, 2.0315).

Optimized for HPC execution on AMD ROCm / RDNA 4 and NVIDIA CUDA via batched FP32 GEMMs (`torch.bmm`).
Provides numerical stability against spectral collapse while preserving orientation for rectangular
matrices (M < N and M > N).
"""

from __future__ import annotations

import torch


def zeropower_via_newtonschulz5(
    G: torch.Tensor,
    steps: int = 5,
    eps: float = 1e-7,
    compute_dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    """Computes the zeroth power of a matrix (nearest orthogonal matrix) using quintic Newton-Schulz iterations.

    Equalizes singular values across update directions to remove ill-conditioned spectral bias.
    Supports 2D (M, N), 3D batched (B, M, N), and higher-dimensional tensors.
    For batched inputs, all Newton-Schulz iterations execute in parallel via batched GEMMs (torch.bmm).

    Args:
        G: Input gradient or matrix tensor of shape (..., M, N) with ndim >= 2.
        steps: Number of quintic Newton-Schulz iterations (default: 5).
        eps: Small constant for numerical stability during Frobenius norm scaling.
        compute_dtype: Intermediate tensor dtype during Newton-Schulz iterations (default: torch.float32
            for maximum spectral stability; can be set to torch.bfloat16 for WMMA/Tensor Core acceleration).

    Returns:
        Orthogonalized tensor with the same shape and dtype as G.
    """
    assert G.ndim >= 2, f"Expected at least 2D tensor, got shape {G.shape}"
    orig_shape = G.shape

    if G.ndim == 2:
        is_2d = True
        X = G.unsqueeze(0)
    elif G.ndim == 3:
        is_2d = False
        X = G
    else:
        is_2d = False
        X = G.reshape(-1, orig_shape[-2], orig_shape[-1])

    B, M, N = X.shape
    a, b, c = (3.4445, -4.7750, 2.0315)
    X = X.to(dtype=compute_dtype)
    norm = torch.linalg.norm(X, dim=(-2, -1), keepdim=True) + eps
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

    out = X.to(dtype=G.dtype)
    if is_2d:
        return out.squeeze(0)
    if G.ndim > 3:
        return out.reshape(orig_shape)
    return out


__all__ = [
    "zeropower_via_newtonschulz5",
]
