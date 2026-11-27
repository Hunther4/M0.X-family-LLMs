"""Unit tests for the modularized src/kernel package and backwards-compatibility shims.

Verifies:
1. Direct imports from `src.kernel` and `kernel`.
2. Clean re-exports from original locations in `src.transformer` and `src.training.optimizer`.
3. Functional verification and forward/backward sanity of all core kernel operators:
   - rms_norm
   - cross_entropy
   - rope
   - swiglu
   - attention dispatcher
   - newton_schulz
"""

import pytest
import torch
import torch.nn.functional as F

# 1. Imports from src.kernel
from src.kernel import (
    RMSNorm,
    fused_rmsnorm,
    fused_add_rmsnorm,
    fused_chunked_cross_entropy,
    FusedCrossEntropyLoss,
    RotaryPositionalEmbedding,
    fused_rope,
    fused_swiglu,
    AttentionBackend,
    AttentionDispatcher,
    zeropower_via_newtonschulz5,
)

# 2. Imports from backwards-compatible original locations
import src.transformer.rms_norm as legacy_rms_norm
import src.transformer.fused_cross_entropy as legacy_ce
import src.transformer.rope as legacy_rope
import src.transformer.fused_ffn as legacy_ffn
import src.transformer.attention_backend as legacy_attn
import src.training.optimizer as legacy_opt


def test_kernel_reexports_identity():
    """Verify that legacy modules re-export the exact same objects as src.kernel."""
    assert legacy_rms_norm.RMSNorm is RMSNorm
    assert legacy_rms_norm.fused_rmsnorm is fused_rmsnorm
    assert legacy_rms_norm.fused_add_rmsnorm is fused_add_rmsnorm

    assert legacy_ce.fused_chunked_cross_entropy is fused_chunked_cross_entropy
    assert legacy_ce.FusedCrossEntropyLoss is FusedCrossEntropyLoss

    assert legacy_rope.RotaryPositionalEmbedding is RotaryPositionalEmbedding
    assert legacy_rope.fused_rope is fused_rope

    assert legacy_ffn.fused_swiglu is fused_swiglu

    assert legacy_attn.AttentionBackend is AttentionBackend
    assert legacy_attn.AttentionDispatcher is AttentionDispatcher

    assert legacy_opt.zeropower_via_newtonschulz5 is zeropower_via_newtonschulz5


def test_newton_schulz_kernel_math():
    """Verify Newton-Schulz 5 zeropower kernel orthogonalizes 2D and 3D tensors."""
    torch.manual_seed(42)
    # 2D case
    G2d = torch.randn(32, 32, dtype=torch.float32)
    X2d = zeropower_via_newtonschulz5(G2d, steps=5)
    assert X2d.shape == (32, 32)
    # Check approximate orthogonality X @ X.T ~ I
    eye = torch.eye(32)
    err = (X2d @ X2d.T - eye).abs().max().item()
    assert err < 0.5, f"Expected near orthogonal matrix, max abs error: {err}"

    # 3D batched case
    G3d = torch.randn(4, 16, 16, dtype=torch.float32)
    X3d = zeropower_via_newtonschulz5(G3d, steps=5)
    assert X3d.shape == (4, 16, 16)
    for b in range(4):
        err_b = (X3d[b] @ X3d[b].T - torch.eye(16)).abs().max().item()
        assert err_b < 0.5


def test_swiglu_kernel_math():
    """Verify SwiGLU activation computes SiLU(g) * u with exact gradients."""
    torch.manual_seed(42)
    g = torch.randn(8, 64, dtype=torch.float32, requires_grad=True)
    u = torch.randn(8, 64, dtype=torch.float32, requires_grad=True)

    out = fused_swiglu(g, u)
    ref = F.silu(g) * u
    assert torch.allclose(out, ref, atol=1e-5)

    loss = out.sum()
    loss.backward()
    assert g.grad is not None
    assert u.grad is not None


def test_rms_norm_kernel_math():
    """Verify RMSNorm forward computation."""
    torch.manual_seed(42)
    x = torch.randn(4, 16, 64, dtype=torch.float32, requires_grad=True)
    norm = RMSNorm(d_model=64)
    y = norm(x)
    assert y.shape == x.shape

    loss = y.sum()
    loss.backward()
    assert x.grad is not None
    assert norm.gamma.grad is not None


def test_rope_kernel_math():
    """Verify Rotary Positional Embedding."""
    class DummyConfig:
        d_head = 32
        rope_theta = 10000.0
        partial_rotary_factor = 1.0

    rope = RotaryPositionalEmbedding(DummyConfig())
    x = torch.randn(2, 8, 4, 32, dtype=torch.float32)
    out = rope(x, offset=0)
    assert out.shape == x.shape


def test_cross_entropy_kernel_math():
    """Verify Fused Chunked Cross-Entropy Loss on CPU eager fallback."""
    torch.manual_seed(42)
    batch, seq_len, d_model, vocab_size = 2, 8, 32, 128
    hidden = torch.randn(batch, seq_len, d_model, dtype=torch.float32, requires_grad=True)
    weight = torch.randn(vocab_size, d_model, dtype=torch.float32, requires_grad=True)
    targets = torch.randint(0, vocab_size, (batch, seq_len), dtype=torch.long)

    loss = fused_chunked_cross_entropy(hidden, weight, targets, chunk_size=4)
    assert loss.ndim == 0
    assert not torch.isnan(loss)
    assert loss.item() > 0.0

    loss.backward()
    assert hidden.grad is not None
    assert weight.grad is not None


def test_attention_dispatcher():
    """Verify AttentionDispatcher defaults and backend validation."""
    dispatcher = AttentionDispatcher(AttentionBackend.AUTO)
    assert dispatcher.preferred_backend == AttentionBackend.AUTO

    q = torch.randn(2, 4, 8, 16)
    k = torch.randn(2, 4, 8, 16)
    v = torch.randn(2, 4, 8, 16)
    out = dispatcher.dispatch(q, k, v, is_causal=True)
    assert out.shape == q.shape
