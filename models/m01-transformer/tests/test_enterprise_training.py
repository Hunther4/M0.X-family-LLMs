"""Tests for Enterprise-Grade Training components: Muon, Hybrid Optimizer, WSD Scheduler, and Sequence Packing."""

import math
import torch
import torch.nn as nn
import pytest

from src.training.optimizer import zeropower_via_newtonschulz5, Muon, EnterpriseHybridOptimizer
from src.training.scheduler import get_wsd_schedule, get_cosine_with_warmup_schedule
from src.training.sequence_packing import PackedSequenceIterator


class TestNewtonSchulzOrthogonalization:
    def test_zeropower_orthogonal_matrix(self):
        # Create random non-orthogonal matrix
        torch.manual_seed(42)
        G = torch.randn(32, 64)
        S_orig = torch.linalg.svdvals(G)
        orig_cond = (S_orig[0] / S_orig[-1]).item()

        X = zeropower_via_newtonschulz5(G, steps=5)
        assert X.shape == G.shape

        S_ns = torch.linalg.svdvals(X)
        ns_cond = (S_ns[0] / S_ns[-1]).item()

        # Newton-Schulz significantly compresses singular value spectrum toward 1.0
        assert ns_cond < orig_cond, f"Expected condition number reduction: {orig_cond} -> {ns_cond}"
        assert S_ns.min().item() > 0.5 and S_ns.max().item() < 1.5


class TestMuonOptimizer:
    def test_muon_step_reduces_loss(self):
        torch.manual_seed(42)
        linear = nn.Linear(32, 16, bias=False)
        opt = Muon(linear.parameters(), lr=0.02, weight_decay=0.01)

        x = torch.randn(8, 32)
        target = torch.randn(8, 16)

        initial_loss = nn.functional.mse_loss(linear(x), target).item()

        for _ in range(5):
            opt.zero_grad()
            loss = nn.functional.mse_loss(linear(x), target)
            loss.backward()
            opt.step()

        final_loss = nn.functional.mse_loss(linear(x), target).item()
        assert final_loss < initial_loss, f"Expected loss decrease with Muon: {initial_loss} -> {final_loss}"


class MockTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(100, 32)
        self.attn_proj = nn.Linear(32, 32, bias=False)  # 2D -> Muon
        self.norm = nn.LayerNorm(32)                    # 1D -> AdamW
        self.router = nn.Linear(32, 4, bias=True)       # router -> AdamW
        self.lm_head = nn.Linear(32, 100, bias=False)   # lm_head -> AdamW


class TestEnterpriseHybridOptimizer:
    def test_parameter_partitioning(self):
        model = MockTransformer()
        opt = EnterpriseHybridOptimizer(model, muon_lr=0.02, adamw_lr=3e-4)

        # Muon should have attn_proj weight
        assert len(opt.muon_params) == 1
        assert opt.muon_params[0] is model.attn_proj.weight

        # AdamW should manage embedding, norm, router, lm_head
        assert len(opt.adamw_decay_params) >= 1
        assert len(opt.adamw_no_decay_params) >= 1

    def test_hybrid_step_and_state_dict(self):
        model = MockTransformer()
        opt = EnterpriseHybridOptimizer(model, muon_lr=0.02, adamw_lr=3e-4)

        x = torch.randint(0, 100, (4, 10))
        emb = model.embedding(x)
        h = model.norm(model.attn_proj(emb))
        logits = model.lm_head(h)
        loss = logits.sum()
        loss.backward()

        opt.step()
        sd = opt.state_dict()
        assert "muon" in sd
        assert "adamw" in sd

        # Test reload
        opt.load_state_dict(sd)


class TestWSDScheduler:
    def test_wsd_phases(self):
        model = nn.Linear(10, 10)
        opt = torch.optim.AdamW(model.parameters(), lr=1.0)
        # 100 total steps: warmup=10, stable=80 (steps 10..80), decay=20 (steps 80..100)
        sched = get_wsd_schedule(opt, warmup_steps=10, max_steps=100, stable_ratio=0.8, min_lr_ratio=0.1)

        # Step 0: Warmup start (> 0.0, 0.1) to avoid nullifying gradients at step 0
        assert math.isclose(sched.get_last_lr()[0], 0.1, abs_tol=1e-5)

        # Step 5: Warmup progression ((5 + 1)/10 = 0.6)
        for _ in range(5):
            sched.step()
        assert math.isclose(sched.get_last_lr()[0], 0.6, abs_tol=1e-5)

        # Step 10: Warmup end -> 1.0
        for _ in range(5):
            sched.step()
        assert math.isclose(sched.get_last_lr()[0], 1.0, abs_tol=1e-5)

        # Step 50: In the middle of stable phase -> 1.0
        for _ in range(40):
            sched.step()
        assert math.isclose(sched.get_last_lr()[0], 1.0, abs_tol=1e-5)

        # Step 80: End of stable phase -> 1.0
        for _ in range(30):
            sched.step()
        assert math.isclose(sched.get_last_lr()[0], 1.0, abs_tol=1e-5)

        # Step 100: Final decayed step -> min_lr_ratio (0.1)
        for _ in range(20):
            sched.step()
        assert math.isclose(sched.get_last_lr()[0], 0.1, abs_tol=1e-4)


class TestSequencePacking:
    def test_zero_waste_sequence_packing(self):
        # 3 documents of lengths 10, 15, 20
        docs = [
            list(range(10)),
            list(range(15)),
            list(range(20)),
        ]
        # Total tokens = (10 + 1) + (15 + 1) + (20 + 1) = 48 tokens
        packer = PackedSequenceIterator(iter(docs), seq_len=16, eot_id=256)
        chunks = list(packer)

        # 48 tokens -> should yield exactly (48 - 1) // 16 = 2 full chunks (32 tokens)
        assert len(chunks) == 2
        inp0, tgt0, mask0 = chunks[0]
        assert inp0.shape == (16,)
        assert tgt0.shape == (16,)
        assert mask0.shape == (16, 16)
        assert mask0.dtype == torch.bool
        # Verify target is shifted by 1
        assert torch.equal(inp0[1:], tgt0[:-1])
        # Verify causal property: position 0 can only attend to itself
        assert mask0[0, 0] == True
        assert mask0[0, 1] == False
        # Verify block-diagonal: position 0 cannot attend to position 11+
        # (doc 1 has 10 tokens + EOT = 11 positions, so pos 11 starts doc 2)
        assert mask0[0, 11] == False
