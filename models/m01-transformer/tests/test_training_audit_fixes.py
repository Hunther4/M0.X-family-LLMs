"""Unit tests for the 14 Training Engine audit fixes and improvements."""

import os
import math
import tempfile
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.training.config import TrainingConfig
from src.training.loop import train, _check_moe_collapse
from src.training.moe_metrics import (
    expert_usage_histogram,
    gini_coefficient,
    imbalance_ratio,
    expert_utilization_pct,
    router_entropy,
    dead_expert_info,
    expert_saturation,
    compute_moe_metrics,
)
from src.training.datasets import AmplifiedDialogueDataset, JsonlDataset
from src.training.dataset import TinyShakespeareDataset, BinaryCorpusDataset
from src.training.optimizer import EnterpriseHybridOptimizer
from src.training.checkpoint import CheckpointManager
from src.training.scheduler import get_wsd_schedule, get_cosine_with_warmup_schedule
from src.training.eval import evaluate_val_loss


# ── 1. AMP scaler unscale and clip_grad_norm_ with config.max_norm ────────────
def test_amp_scaler_unscale_and_grad_clipping():
    """Verify that under AMP, scaler.unscale_ is called before clip_grad_norm_."""
    model = nn.Linear(4, 2)
    data = TensorDataset(torch.randn(4, 4), torch.randint(0, 2, (4,)))
    loader = DataLoader(data, batch_size=2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()
    config = TrainingConfig(max_norm=0.75, log_interval=10)

    scaler = MagicMock()
    # Mock scale(loss).backward()
    scaled_loss = MagicMock()
    scaler.scale.return_value = scaled_loss

    with patch("torch.nn.utils.clip_grad_norm_") as mock_clip:
        mock_clip.return_value = torch.tensor(0.5)
        # Mock autocast context manager for cpu device
        result = train(
            model=model,
            dataloader=loader,
            optimizer=optimizer,
            criterion=criterion,
            steps=2,
            device=torch.device("cpu"),
            scaler=scaler,
            config=config,
        )

        assert scaler.unscale_.called
        scaler.unscale_.assert_called_with(optimizer)
        assert mock_clip.called
        assert mock_clip.call_args[1]["max_norm"] == 0.75
        assert scaler.step.called
        assert scaler.update.called
        assert result["steps_completed"] == 2


# ── 2. Empty dataloader & step counter off-by-one ─────────────────────────────
def test_empty_dataloader_does_not_loop_infinitely():
    """Empty dataloader should immediately exit and return steps_completed == 0."""
    model = nn.Linear(4, 2)
    loader = []  # empty dataloader
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    result = train(
        model=model,
        dataloader=loader,
        optimizer=optimizer,
        criterion=criterion,
        steps=10,
        device=torch.device("cpu"),
    )
    assert result["steps_completed"] == 0
    assert result["last_loss"] == 0.0


def test_target_loss_step_count_exact():
    """When target_loss triggers on step 1, steps_completed should be 1, not 0."""
    model = nn.Linear(4, 2)
    data = TensorDataset(torch.randn(8, 4), torch.randint(0, 2, (8,)))
    loader = DataLoader(data, batch_size=2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    # Target loss huge so it triggers on first batch
    result = train(
        model=model,
        dataloader=loader,
        optimizer=optimizer,
        criterion=criterion,
        steps=10,
        device=torch.device("cpu"),
        target_loss=999.0,
    )
    assert result["steps_completed"] == 1


# ── 3. MoE collapse decoupled from log_interval ───────────────────────────────
def test_moe_collapse_decoupled_from_log_interval():
    """MoE collapse should trigger at collapse_streak_threshold steps, even if log_interval is large."""
    class FakeMoE(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(4, 2)
        def forward(self, x):
            return self.linear(x)
        def get_moe_metrics(self):
            return {
                "layer_0/histogram": [0, 0, 10, 10],  # 2 dead experts -> ratio 0.5
                "global/n_layers_moe": 1,
            }

    model = FakeMoE()
    data = TensorDataset(torch.randn(20, 4), torch.randint(0, 2, (20,)))
    loader = DataLoader(data, batch_size=2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    # log_interval is 100, but collapse threshold is 3
    result = train(
        model=model,
        dataloader=loader,
        optimizer=optimizer,
        criterion=criterion,
        steps=50,
        device=torch.device("cpu"),
        log_interval=100,
        config=TrainingConfig(
            moe_collapse_consecutive_steps=3,
            moe_collapse_expert_ratio=0.3,
        ),
    )
    assert result["steps_completed"] == 3
    assert "Router collapse in layer_0/histogram at step 3" in result["stop_reason"]


# ── 4. Coherent router collapse condition in moe_metrics.py ───────────────────
def test_moe_metrics_coherent_router_collapse():
    """Router collapse should be detected if dead expert ratio >= 0.8 in any layer."""
    class DummyBlock(nn.Module):
        def __init__(self, num_experts, top_k, dead_ratio):
            super().__init__()
            self.ff = nn.Module()
            self.ff.num_experts = num_experts
            self.ff.moe_top_k = top_k
            self.ff.gate_probs = torch.ones(4, num_experts) / num_experts
            self.ff.gate_logits = torch.ones(4, num_experts)
            # Create topk_indices where only 1 expert is used if dead_ratio is high
            active = max(1, int(num_experts * (1.0 - dead_ratio)))
            self.ff.topk_indices = torch.zeros(4, top_k, dtype=torch.long)
            self.ff.get_aux_loss = lambda: torch.tensor(0.01)

    class DummyModel(nn.Module):
        def __init__(self, dead_ratio=0.85):
            super().__init__()
            self.config = MagicMock(num_experts=8, moe_top_k=1, num_shared_experts=0)
            self.blocks = nn.ModuleList([
                DummyBlock(8, 1, dead_ratio=dead_ratio),
            ])

    # With 85% dead experts, collapse should be True
    m_collapse = DummyModel(dead_ratio=0.85)
    metrics_collapse = compute_moe_metrics(m_collapse)
    assert metrics_collapse["global/router_collapse"] is True

    # With 0% dead experts (all active), collapse should be False
    m_healthy = DummyModel(dead_ratio=0.0)
    # Set all 8 experts active across 8 tokens
    m_healthy.blocks[0].ff.topk_indices = torch.arange(8).unsqueeze(1)
    m_healthy.blocks[0].ff.gate_probs = torch.ones(8, 8) / 8
    m_healthy.blocks[0].ff.gate_logits = torch.ones(8, 8)
    metrics_healthy = compute_moe_metrics(m_healthy)
    assert metrics_healthy["global/router_collapse"] is False


# ── 5. JsonlDataset configurable / dynamic EOS ────────────────────────────────
def test_jsonl_dataset_dynamic_eos():
    """JsonlDataset should respect custom eos_token or tokenizer eos_token_id."""
    class DummyTokenizer:
        eos_token_id = 9999
        special_tokens = {"<|endoftext|>": 9999}
        def encode(self, text):
            return [1, 2, 3]

    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        import json
        f.write(json.dumps({"system": "sys", "conversation": "conv"}) + "\n")
        tmp_name = f.name

    try:
        ds = JsonlDataset(tokenizer=DummyTokenizer(), paths=[tmp_name], seq_len=2)
        assert ds.eos_token == 9999
        assert ds.tokens[-1].item() == 9999

        ds_explicit = JsonlDataset(tokenizer=DummyTokenizer(), paths=[tmp_name], seq_len=2, eos_token=777)
        assert ds_explicit.eos_token == 777
        assert ds_explicit.tokens[-1].item() == 777
    finally:
        os.unlink(tmp_name)


# ── 6. Optimizer CPU / CUDA fused AdamW check ─────────────────────────────────
def test_optimizer_fused_adamw_disabled_on_cpu():
    """EnterpriseHybridOptimizer must not set fused=True on CPU parameters even if CUDA is available."""
    model = nn.Sequential(nn.Linear(8, 8, bias=True))
    with patch("torch.cuda.is_available", return_value=True):
        opt = EnterpriseHybridOptimizer(model, use_fused_adamw=True)
        # Model is on CPU, so fused must be False
        if opt.adamw_opt is not None:
            assert opt.adamw_opt.defaults.get("fused", False) is False


# ── 7. BinaryCorpusDataset lazy memmap and multiprocessing safety ──────────────
def test_binary_corpus_lazy_memmap():
    """BinaryCorpusDataset should lazily initialize memmaps and support serialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "shard_00000.bin")
        arr = np.arange(100, dtype=">u2")
        arr.tofile(path)

        cfg = TrainingConfig(seq_len=10)
        ds = BinaryCorpusDataset(cfg, tmpdir)
        # At init, _shard_mmaps has None entries
        assert ds._shard_mmaps[0] is None

        # Accessing an element triggers lazy open
        item_x, item_y = ds[0]
        assert len(item_x) == 10
        assert ds._shard_mmaps[0] is not None

        # Serialization test (pickle for multiprocessing)
        import pickle
        serialized = pickle.dumps(ds)
        ds_restored = pickle.loads(serialized)
        assert ds_restored._shard_mmaps[0] is None
        x_res, _ = ds_restored[0]
        assert torch.equal(item_x, x_res)
        ds.close()
        ds_restored.close()


# ── 8. CheckpointManager map_location support ─────────────────────────────────
def test_checkpoint_manager_map_location():
    """CheckpointManager.load should accept map_location parameter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = CheckpointManager(tmpdir)
        model = nn.Linear(4, 2)
        opt = torch.optim.SGD(model.parameters(), lr=0.01)
        sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: 1.0)
        mgr.save(step=1, model=model, optimizer=opt, scheduler=sched, loss=0.5, config={})

        with patch("src.training.checkpoint.safe_load_checkpoint") as mock_safe_load:
            mock_safe_load.return_value = {
                "epoch": 0, "step": 1, "loss": 0.5, "config": {},
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": opt.state_dict(),
                "scheduler_state_dict": sched.state_dict(),
            }
            loaded = mgr.load(model, opt, sched, map_location="cpu")
            assert mock_safe_load.called
            assert mock_safe_load.call_args[1]["map_location"] == "cpu"
            assert loaded["step"] == 1


# ── 9. TinyShakespeareDataset data_dir direct file & preallocation ─────────────
def test_tiny_shakespeare_direct_file_path():
    """TinyShakespeareDataset should handle data_dir pointing directly to a text file."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("A" * 500)
        tmp_name = f.name

    try:
        cfg = TrainingConfig(seq_len=32, data_dir=tmp_name)
        ds = TinyShakespeareDataset(cfg)
        assert len(ds) > 0
        assert ds.source_files == [tmp_name]
    finally:
        os.unlink(tmp_name)


def test_binary_corpus_load_to_ram_preallocation():
    """BinaryCorpusDataset with load_to_ram should preallocate a contiguous buffer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tokens = list(range(200))
        path = os.path.join(tmpdir, "shard_00000.bin")
        np.array(tokens, dtype=">u2").tofile(path)

        cfg = TrainingConfig(seq_len=16)
        ds = BinaryCorpusDataset(cfg, tmpdir, load_to_ram=True)
        assert ds.data is not None
        assert ds.data.dtype == np.dtype(">u2")
        assert len(ds.data) == 200
        ds.close()


# ── 10. AmplifiedDialogueDataset modular indexing ─────────────────────────────
def test_amplified_dialogue_virtual_amplification():
    """AmplifiedDialogueDataset should not replicate tokens in RAM; uses modular indexing."""
    class DummyTokenizer:
        def encode(self, text):
            return list(range(len(text)))

    dialogues = ["abcde", "fghij"]
    # 2 dialogues of ~15 chars each -> ~30 tokens base
    ds = AmplifiedDialogueDataset(DummyTokenizer(), dialogues, amp_factor=10, seq_len=8)
    base_token_len = len(ds.tokens)

    # Amplification factor of 10 should increase dataset len by 10x, but NOT token buffer
    assert len(ds) == ds.base_len * 10
    assert len(ds.tokens) == base_token_len

    # Access beyond base_len
    x0, y0 = ds[0]
    x_wrap, y_wrap = ds[ds.base_len]  # wraps back to 0
    assert torch.equal(x0, x_wrap)
    assert torch.equal(y0, y_wrap)


# ── 11. moe_metrics histogram caching & entropy clamp ─────────────────────────
def test_moe_metrics_histogram_caching_and_entropy_clamp():
    """Histogram is cached to avoid repeated bincount, and entropy uses clamp(min=1e-9)."""
    class DummyMoE(nn.Module):
        def __init__(self):
            super().__init__()
            self.num_experts = 4
            self.topk_indices = torch.tensor([[0, 1], [0, 2], [1, 2]])
            # Zero probability in some entries to test clamp(min=1e-9)
            self.gate_probs = torch.tensor([[1.0, 0.0, 0.0, 0.0], [0.5, 0.5, 0.0, 0.0], [0.0, 0.5, 0.5, 0.0]])

    moe = DummyMoE()
    # Test router_entropy does not return NaN even with 0.0 probability
    ent = router_entropy(moe)
    assert not math.isnan(ent)
    assert ent >= 0.0

    # Test histogram caching: passing cached list avoids bincount
    cached_hist = [10, 5, 5, 0]
    assert expert_usage_histogram(moe, hist=cached_hist) == cached_hist
    assert gini_coefficient(moe, hist=cached_hist) >= 0.0
    assert imbalance_ratio(moe, hist=cached_hist) == 10.0 / 5.0
    util = expert_utilization_pct(moe, capacity=10, hist=cached_hist)
    assert util[0] == 1.0
    dead = dead_expert_info(moe, hist=cached_hist)
    assert dead["dead_count"] == 1
    assert dead["dead_ids"] == [3]


# ── 12. Scheduler warmup at step 0 is non-zero ────────────────────────────────
def test_scheduler_warmup_step_zero_positive():
    """Warmup LR at step 0 must be > 0 so initial step update is not multiplied by zero."""
    param = nn.Parameter(torch.ones(1))
    opt = torch.optim.SGD([param], lr=1.0)
    sched = get_wsd_schedule(opt, warmup_steps=10, max_steps=100)
    # At step 0, lr should be (0 + 1) / 10 = 0.1
    assert sched.get_last_lr()[0] == 0.1

    opt_cos = torch.optim.SGD([param], lr=1.0)
    sched_cos = get_cosine_with_warmup_schedule(opt_cos, warmup_steps=10, max_steps=100)
    assert sched_cos.get_last_lr()[0] == 0.1


# ── 13. TrainingConfig from_yaml handles null training section ────────────────
def test_training_config_from_yaml_null_or_fallback():
    """TrainingConfig.from_yaml handles YAML files where training is null or root."""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write("batch_size: 16\nmax_lr: 0.001\n")
        flat_yaml = f.name

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write("training:\n  batch_size: 32\n")
        nested_yaml = f.name

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write("training: null\n")
        null_yaml = f.name

    try:
        cfg_flat = TrainingConfig.from_yaml(flat_yaml)
        assert cfg_flat.batch_size == 16
        assert cfg_flat.max_lr == 0.001

        cfg_nested = TrainingConfig.from_yaml(nested_yaml)
        assert cfg_nested.batch_size == 32

        cfg_null = TrainingConfig.from_yaml(null_yaml)
        assert isinstance(cfg_null, TrainingConfig)
    finally:
        os.unlink(flat_yaml)
        os.unlink(nested_yaml)
        os.unlink(null_yaml)


# ── 14. eval.py preserves model.training state ────────────────────────────────
def test_evaluate_val_loss_preserves_training_mode():
    """evaluate_val_loss must restore original model.training state."""
    model = nn.Linear(4, 2)
    data = TensorDataset(torch.randn(4, 4), torch.randint(0, 2, (4,)))
    loader = DataLoader(data, batch_size=2)
    criterion = nn.CrossEntropyLoss()

    # Case A: Model in train mode
    model.train(True)
    _ = evaluate_val_loss(model, loader, torch.device("cpu"), criterion)
    assert model.training is True

    # Case B: Model in eval mode
    model.train(False)
    _ = evaluate_val_loss(model, loader, torch.device("cpu"), criterion)
    assert model.training is False
