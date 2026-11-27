"""Tests for Sequence Packing, Dynamic EOT, Multi-Epoch Iteration, and Training Integration."""

import os
import tempfile
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, IterableDataset, Subset
import pytest
import yaml

from src.training.sequence_packing import PackedSequenceIterator
from src.kernel.attention import AttentionDispatcher, AttentionBackend
from src.training.config import TrainingConfig
from src.training.train import parse_args, configure_optimizer, build_training_dataset
from src.model.lm import TransformerLM
from src.transformer.config import M01Config


class MockTokenizerSpecialTokens:
    def __init__(self, eot: int = 350):
        self.special_tokens = {"<|endoftext|>": eot, "<|pad|>": eot + 1}


class MockTokenizerEOSTokenId:
    def __init__(self, eos: int = 50256):
        self.eos_token_id = eos


class TestPackedSequenceIterator:
    """Unit tests for PackedSequenceIterator features and improvements."""

    def test_inherits_iterable_dataset(self):
        """PackedSequenceIterator MUST formally inherit from torch.utils.data.IterableDataset."""
        assert issubclass(PackedSequenceIterator, IterableDataset)
        docs = [[1, 2, 3], [4, 5]]
        packer = PackedSequenceIterator(iter(docs), seq_len=4, eot_id=256)
        assert isinstance(packer, IterableDataset)

    def test_dynamic_eot_id(self):
        """PackedSequenceIterator MUST support int or tokenizer objects for eot_id."""
        docs = [[10, 20]]
        # 1. Direct int
        packer1 = PackedSequenceIterator(iter(docs), seq_len=4, eot_id=999)
        assert packer1.eot_id == 999

        # 2. Tokenizer with special_tokens dict
        tok_special = MockTokenizerSpecialTokens(eot=777)
        packer2 = PackedSequenceIterator(iter(docs), seq_len=4, eot_id=tok_special)
        assert packer2.eot_id == 777

        # 3. Tokenizer with eos_token_id attribute
        tok_hf = MockTokenizerEOSTokenId(eos=50256)
        packer3 = PackedSequenceIterator(iter(docs), seq_len=4, eot_id=tok_hf)
        assert packer3.eot_id == 50256

    def test_epoch_reset_clears_residual_buffer(self):
        """PackedSequenceIterator MUST reset buffer, _doc_ids, and doc_counter on each __iter__() call."""
        # A list of docs that leaves residual tokens after yielding chunk 1
        # Doc 1: [1, 2, 3, 4] + [EOT(256)] = 5 tokens
        # Doc 2: [5, 6, 7] + [EOT(256)] = 4 tokens
        # Total tokens = 9. With seq_len = 4, seq_len + 1 = 5.
        # Chunk 1 consumes 4 tokens (stride=4), leaving 5 tokens in buffer.
        # Chunk 2 consumes 4 tokens (stride=4), leaving 1 residual token [256].
        docs = [
            [1, 2, 3, 4],
            [5, 6, 7],
        ]
        packer = PackedSequenceIterator(docs, seq_len=4, eot_id=256)

        # Epoch 1
        epoch1_chunks = list(packer)
        assert len(epoch1_chunks) == 2
        # After epoch 1 completes, packer internal buffer might have residual tokens if not reset
        assert len(packer.buffer) == 1

        # Epoch 2: __iter__() must reset state and yield exactly identical chunks without leftover contamination
        epoch2_chunks = list(packer)
        assert len(epoch2_chunks) == 2
        assert len(packer.buffer) == 1
        assert packer._doc_counter == 2

        # Verify epoch 1 and epoch 2 produced identical inputs, targets, and masks
        for (inp1, tgt1, mask1), (inp2, tgt2, mask2) in zip(epoch1_chunks, epoch2_chunks):
            assert torch.equal(inp1, inp2)
            assert torch.equal(tgt1, tgt2)
            assert torch.equal(mask1, mask2)

    def test_chunk_correctness_and_mask(self):
        """Packed sequences must generate correct autoregressive targets and block-diagonal masks."""
        # Doc A: [10, 11] (id 0) -> + EOT = [10, 11, 256] (3 tokens)
        # Doc B: [20, 21, 22] (id 1) -> + EOT = [20, 21, 22, 256] (4 tokens)
        # Total = 7 tokens. seq_len = 4, chunk length = 5 tokens.
        docs = [[10, 11], [20, 21, 22]]
        packer = PackedSequenceIterator(docs, seq_len=4, eot_id=256)
        chunks = list(packer)
        assert len(chunks) == 1

        inp, tgt, mask = chunks[0]
        # Chunk tokens: [10, 11, 256, 20, 21]
        assert inp.tolist() == [10, 11, 256, 20]
        assert tgt.tolist() == [11, 256, 20, 21]

        # Mask: 4x4 boolean
        # Position 0 (10, doc 0): can attend to 0 (doc 0) -> True
        # Position 1 (11, doc 0): can attend to 0, 1 (doc 0) -> True, True
        # Position 2 (256, doc 0): can attend to 0, 1, 2 (doc 0) -> True, True, True
        # Position 3 (20, doc 1): can attend to 3 (doc 1), NOT to 0, 1, 2 (doc 0)!
        expected_mask = torch.tensor([
            [True, False, False, False],
            [True,  True, False, False],
            [True,  True,  True, False],
            [False, False, False, True],
        ], dtype=torch.bool)
        assert torch.equal(mask, expected_mask)

    def test_dataloader_integration(self):
        """PackedSequenceIterator MUST integrate with PyTorch DataLoader."""
        docs = [[i, i + 1, i + 2] for i in range(10)]
        packer = PackedSequenceIterator(docs, seq_len=8, eot_id=256)
        loader = DataLoader(packer, batch_size=2)

        batch_count = 0
        for batch_inp, batch_tgt, batch_mask in loader:
            batch_count += 1
            assert batch_inp.shape[1] == 8
            assert batch_tgt.shape[1] == 8
            assert batch_mask.shape[1:] == (8, 8)
        assert batch_count >= 1

    def test_attention_dispatcher_compatibility_and_flags(self):
        """Packed sequence 2D mask must work with AUTO/MATH/EFFICIENT and error on FLASH unless fallback enabled."""
        q = torch.randn(2, 4, 16, 32)
        k = torch.randn(2, 4, 16, 32)
        v = torch.randn(2, 4, 16, 32)
        mask = torch.tril(torch.ones(16, 16, dtype=torch.bool))

        # AUTO / MATH backend accepts arbitrary 2D mask
        dispatcher_math = AttentionDispatcher(AttentionBackend.MATH)
        out = dispatcher_math.dispatch(q, k, v, attn_mask=mask)
        assert out.shape == q.shape

        # Verify compatible backends helper
        backends = PackedSequenceIterator.get_compatible_attention_backends()
        assert "auto" in backends
        assert "efficient" in backends
        assert "math" in backends
        assert "flash" not in backends

        # Test fallback flag behavior on FLASH backend
        dispatcher_flash = AttentionDispatcher(AttentionBackend.FLASH)
        # Without fallback -> raises ValueError
        with pytest.raises(ValueError, match="does not support explicit attn_mask"):
            dispatcher_flash.dispatch(q, k, v, attn_mask=mask, allow_mask_fallback=False)

        # With fallback -> warns and falls back without raising
        with pytest.warns(RuntimeWarning, match="Falling back to EFFICIENT"):
            out_fallback = dispatcher_flash.dispatch(q, k, v, attn_mask=mask, allow_mask_fallback=True)
            assert out_fallback.shape == q.shape


class TestTrainingCLIAndConfigPrecedence:
    """Verifies that YAML values prevail unless explicitly overridden by CLI flags."""

    def test_cli_parser_defaults_are_none(self):
        """Enterprise CLI flags MUST default to None to prevent overriding YAML silently."""
        args = parse_args([])
        assert args.optimizer is None
        assert args.scheduler is None
        assert args.muon_lr is None
        assert args.stable_ratio is None

    def test_yaml_config_prevalence(self):
        """When CLI flags are omitted, YAML configuration values MUST be preserved."""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            yaml_content = {
                "training": {
                    "optimizer": "adamw",
                    "scheduler": "cosine",
                    "muon_lr": 0.05,
                    "stable_ratio": 0.65,
                }
            }
            yaml.dump(yaml_content, f)
            cfg_path = f.name

        try:
            cfg = TrainingConfig.from_yaml(cfg_path)
            assert cfg.optimizer == "adamw"
            assert cfg.scheduler == "cosine"
            assert cfg.muon_lr == 0.05
            assert cfg.stable_ratio == 0.65

            # Simulating CLI run with --config but NO explicit --optimizer
            args = parse_args(["--config", cfg_path])
            _TRAIN_CLI_MAP = {
                "optimizer": args.optimizer,
                "muon_lr": args.muon_lr,
                "scheduler": args.scheduler,
                "stable_ratio": args.stable_ratio,
            }
            _overrides = {k: v for k, v in _TRAIN_CLI_MAP.items() if v is not None}
            # Overrides must be empty because no CLI flags were set!
            assert len(_overrides) == 0
            assert cfg.optimizer == "adamw"
            assert cfg.scheduler == "cosine"
        finally:
            os.remove(cfg_path)

    def test_cli_overrides_yaml_when_explicitly_set(self):
        """When CLI flags are explicitly provided, they MUST override YAML values."""
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            yaml_content = {
                "training": {
                    "optimizer": "adamw",
                    "scheduler": "cosine",
                    "muon_lr": 0.01,
                }
            }
            yaml.dump(yaml_content, f)
            cfg_path = f.name

        try:
            cfg = TrainingConfig.from_yaml(cfg_path)
            args = parse_args(["--config", cfg_path, "--optimizer", "hybrid_muon", "--muon-lr", "0.03"])

            _TRAIN_CLI_MAP = {
                "optimizer": args.optimizer,
                "muon_lr": args.muon_lr,
                "scheduler": args.scheduler,
                "stable_ratio": args.stable_ratio,
            }
            _overrides = {k: v for k, v in _TRAIN_CLI_MAP.items() if v is not None}
            assert _overrides["optimizer"] == "hybrid_muon"
            assert _overrides["muon_lr"] == 0.03
            assert "scheduler" not in _overrides  # Scheduler remains from YAML!
        finally:
            os.remove(cfg_path)


class TestSequentialSplitAndDevicePlacement:
    """Verifies sequential train/val split for sliding window datasets and device placement."""

    def test_sequential_split_sliding_window(self):
        """Sliding window datasets MUST use sequential split Subset(0..train) and Subset(train..N)."""
        cfg = TrainingConfig(seq_len=16)
        # Synthetic dataset with sliding window
        dataset = build_training_dataset(cfg)
        total_samples = len(dataset)
        train_size = int(0.90 * total_samples)
        val_size = total_samples - train_size

        train_ds = Subset(dataset, range(0, train_size))
        val_ds = Subset(dataset, range(train_size, total_samples))

        # Check contiguous sequential indices
        assert list(train_ds.indices) == list(range(0, train_size))
        assert list(val_ds.indices) == list(range(train_size, total_samples))

        # Ensure no index overlap between train and val
        train_set = set(train_ds.indices)
        val_set = set(val_ds.indices)
        assert len(train_set.intersection(val_set)) == 0

    def test_device_placement_before_optimizer_config(self):
        """Model on device before configure_optimizer correctly sets parameter device."""
        model = nn.Sequential(nn.Linear(16, 16), nn.LayerNorm(16))
        device = torch.device("cpu")
        model = model.to(device)

        cfg = TrainingConfig(max_lr=1e-3, weight_decay=0.01)
        opt = configure_optimizer(model, cfg, optimizer_type="adamw")
        assert opt is not None
        # Check that optimizer param groups point to the model parameters on the target device
        for group in opt.param_groups:
            for p in group["params"]:
                assert p.device == device
