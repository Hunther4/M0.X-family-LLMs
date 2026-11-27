"""Unit and integration tests for Fused Chunked Cross-Entropy with Triton.

Validates:
1. Strict mathematical parity against PyTorch F.cross_entropy in float32, bfloat16, float16.
2. Gradient parity w.r.t hidden states and embedding weights.
3. Correct behavior of ignore_index = -100 (zero loss and zero gradient).
4. Peak VRAM reduction against the unchunked baseline.
5. Integration with TransformerLM (return_hidden / forward_hidden) and LossPipeline.
"""

import pytest
import torch
import torch.nn.functional as F

from src.transformer.fused_cross_entropy import (
    HAS_TRITON,
    fused_chunked_cross_entropy,
    FusedChunkedCrossEntropyFunction,
    FusedCrossEntropyLoss,
)
from src.engine_v2.loss_pipeline import FusedChunkedCrossEntropyLossTerm, LossPipeline
from src.transformer.config import M01Config
from src.model.lm import TransformerLM


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@pytest.mark.skipif(not torch.cuda.is_available() or not HAS_TRITON, reason="CUDA and Triton required")
@pytest.mark.parametrize("dtype", [torch.float32, torch.bfloat16, torch.float16])
@pytest.mark.parametrize("chunk_size", [32, 64, 256])
def test_mathematical_parity_and_gradients(dtype, chunk_size):
    """Verify strict mathematical parity and analytical gradients against PyTorch reference."""
    torch.manual_seed(42)
    N, D, V = 128, 64, 2048

    H = torch.randn(N, D, device=DEVICE, dtype=dtype, requires_grad=True)
    W = torch.randn(V, D, device=DEVICE, dtype=dtype, requires_grad=True)
    Y = torch.randint(0, V, (N,), device=DEVICE)

    # Sprinkle ignore_index tokens
    Y[0] = -100
    Y[15] = -100
    Y[60] = -100

    # Reference PyTorch computation
    H_ref = H.clone().detach().to(dtype).requires_grad_(True)
    W_ref = W.clone().detach().to(dtype).requires_grad_(True)

    logits_ref = torch.matmul(H_ref, W_ref.t())
    # Upcast reference loss to float32 for clean comparison with online LogSumExp
    loss_ref = F.cross_entropy(logits_ref.float(), Y, ignore_index=-100, reduction="mean")
    loss_ref.backward()

    # Fused chunked computation
    H_fused = H.clone().detach().requires_grad_(True)
    W_fused = W.clone().detach().requires_grad_(True)

    loss_fused = fused_chunked_cross_entropy(
        H_fused, W_fused, Y, ignore_index=-100, chunk_size=chunk_size
    )
    loss_fused.backward()

    # Numerical tolerances per dtype
    if dtype == torch.float32:
        loss_atol = 1e-5
        grad_atol = 1e-5
    elif dtype == torch.bfloat16:
        loss_atol = 5e-2
        grad_atol = 5e-3
    else:  # float16
        loss_atol = 1e-2
        grad_atol = 1e-3

    loss_diff = (loss_ref - loss_fused.float()).abs().item()
    assert loss_diff < loss_atol, f"Loss mismatch for {dtype}: diff={loss_diff:.6e} >= {loss_atol}"

    assert H_fused.grad is not None, f"grad_H is None for {dtype}"
    grad_H_diff = (H_ref.grad.float() - H_fused.grad.float()).abs().max().item()
    assert grad_H_diff < grad_atol, f"grad_H mismatch for {dtype}: diff={grad_H_diff:.6e} >= {grad_atol}"

    assert W_fused.grad is not None, f"grad_W is None for {dtype}"
    grad_W_diff = (W_ref.grad.float() - W_fused.grad.float()).abs().max().item()
    assert grad_W_diff < grad_atol, f"grad_W mismatch for {dtype}: diff={grad_W_diff:.6e} >= {grad_atol}"


@pytest.mark.skipif(not torch.cuda.is_available() or not HAS_TRITON, reason="CUDA and Triton required")
def test_ignore_index_zeros_loss_and_gradient():
    """Verify that tokens with ignore_index produce 0 loss contribution and 0 gradient."""
    torch.manual_seed(123)
    N, D, V = 64, 32, 512

    H = torch.randn(N, D, device=DEVICE, dtype=torch.float32, requires_grad=True)
    W = torch.randn(V, D, device=DEVICE, dtype=torch.float32, requires_grad=True)
    Y = torch.randint(0, V, (N,), device=DEVICE)

    ignored_indices = [5, 10, 20, 25, 40]
    for idx in ignored_indices:
        Y[idx] = -100

    loss = fused_chunked_cross_entropy(H, W, Y, ignore_index=-100, chunk_size=16)
    loss.backward()

    # Gradients for ignored token rows in H should be exactly zero
    assert H.grad is not None
    for idx in ignored_indices:
        grad_row = H.grad[idx]
        assert (grad_row == 0.0).all(), f"Row {idx} should have zero gradient, got {grad_row.abs().max().item()}"


@pytest.mark.skipif(not torch.cuda.is_available() or not HAS_TRITON, reason="CUDA and Triton required")
def test_all_ignored_tokens():
    """Verify edge case where all tokens are ignored (n_valid == 0)."""
    N, D, V = 32, 16, 256
    H = torch.randn(N, D, device=DEVICE, dtype=torch.float32, requires_grad=True)
    W = torch.randn(V, D, device=DEVICE, dtype=torch.float32, requires_grad=True)
    Y = torch.full((N,), -100, device=DEVICE, dtype=torch.long)

    loss = fused_chunked_cross_entropy(H, W, Y, ignore_index=-100, chunk_size=16)
    assert loss.item() == 0.0, f"Expected 0.0 loss for all-ignored, got {loss.item()}"

    loss.backward()
    assert H.grad is not None
    assert W.grad is not None
    assert (H.grad == 0.0).all()
    assert (W.grad == 0.0).all()


@pytest.mark.skipif(not torch.cuda.is_available() or not HAS_TRITON, reason="CUDA and Triton required")
def test_peak_vram_reduction():
    """Verify that chunked fused cross-entropy significantly reduces peak VRAM compared to standard cross-entropy."""
    N, D, V = 4096, 512, 32768
    chunk_size = 512
    dtype = torch.bfloat16

    # 1. Standard PyTorch execution
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    H_std = torch.randn(N, D, device=DEVICE, dtype=dtype, requires_grad=True)
    W_std = torch.randn(V, D, device=DEVICE, dtype=dtype, requires_grad=True)
    Y_std = torch.randint(0, V, (N,), device=DEVICE)

    logits_std = torch.matmul(H_std, W_std.t())
    loss_std = F.cross_entropy(logits_std, Y_std)
    loss_std.backward()
    torch.cuda.synchronize()
    peak_mem_standard = torch.cuda.max_memory_allocated()

    del H_std, W_std, Y_std, logits_std, loss_std
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    # 2. Fused chunked execution
    H_fused = torch.randn(N, D, device=DEVICE, dtype=dtype, requires_grad=True)
    W_fused = torch.randn(V, D, device=DEVICE, dtype=dtype, requires_grad=True)
    Y_fused = torch.randint(0, V, (N,), device=DEVICE)

    loss_fused = fused_chunked_cross_entropy(
        H_fused, W_fused, Y_fused, chunk_size=chunk_size
    )
    loss_fused.backward()
    torch.cuda.synchronize()
    peak_mem_fused = torch.cuda.max_memory_allocated()

    del H_fused, W_fused, Y_fused, loss_fused
    torch.cuda.empty_cache()

    mem_saving_pct = (1.0 - peak_mem_fused / peak_mem_standard) * 100.0

    print(f"\nPeak VRAM - Standard: {peak_mem_standard / 1e6:.2f} MB | Fused Chunked: {peak_mem_fused / 1e6:.2f} MB")
    print(f"VRAM Reduction: {mem_saving_pct:.2f}%")

    # Assert that peak VRAM was reduced by at least 30%
    assert peak_mem_fused < peak_mem_standard, "Fused chunked cross entropy did not reduce peak VRAM"
    assert mem_saving_pct >= 30.0, f"Expected >= 30% VRAM saving, got {mem_saving_pct:.2f}%"


def test_fused_cross_entropy_loss_module():
    """Verify nn.Module wrapper FusedCrossEntropyLoss."""
    criterion = FusedCrossEntropyLoss(ignore_index=-100, chunk_size=32)
    H = torch.randn(64, 32, device=DEVICE, dtype=torch.float32, requires_grad=True)
    W = torch.randn(128, 32, device=DEVICE, dtype=torch.float32, requires_grad=True)
    Y = torch.randint(0, 128, (64,), device=DEVICE)

    loss = criterion(H, W, Y)
    assert loss.dim() == 0
    loss.backward()
    assert H.grad is not None
    assert W.grad is not None


def test_transformer_lm_forward_hidden_and_loss_pipeline():
    """Verify TransformerLM.forward(return_hidden=True) and FusedChunkedCrossEntropyLossTerm."""
    config = M01Config(
        vocab_size=256,
        d_model=64,
        n_layers=2,
        n_heads=2,
        d_ff=128,
        context_length=64,
    )
    model = TransformerLM(config).to(DEVICE)
    model.train()

    input_ids = torch.randint(0, config.vocab_size, (2, 16), device=DEVICE)
    targets = torch.randint(0, config.vocab_size, (2, 16), device=DEVICE)

    # 1. Test standard forward (logits)
    logits = model(input_ids)
    assert logits.shape == (2, 16, config.vocab_size)

    # 2. Test forward with return_hidden=True
    hidden = model(input_ids, return_hidden=True)
    assert hidden.shape == (2, 16, config.d_model)

    # 3. Test forward_hidden method
    hidden2 = model.forward_hidden(input_ids)
    assert torch.allclose(hidden, hidden2)

    # 4. Test LossPipeline with FusedChunkedCrossEntropyLossTerm
    pipeline = LossPipeline([
        FusedChunkedCrossEntropyLossTerm(chunk_size=16)
    ])
    loss = pipeline(hidden, targets, model=model)
    assert loss.dim() == 0
    assert "FusedChunkedCrossEntropy" in pipeline.last_breakdown

    loss.backward()
    # Check that embedding weights received gradients
    assert model.embedding.embedding.weight.grad is not None
    assert torch.isfinite(model.embedding.embedding.weight.grad).all()
