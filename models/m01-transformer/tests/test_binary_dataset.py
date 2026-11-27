"""Unit tests for the optimized BinaryCorpusDataset."""

import os
import tempfile
import numpy as np
import pytest
import torch

from src.training.config import TrainingConfig
from src.training.dataset import BinaryCorpusDataset


def create_mock_shards(tmpdir: str, shard_tokens_list: list[list[int]]) -> list[str]:
    """Helper to create dummy >u2 binary shards."""
    paths = []
    for i, tokens in enumerate(shard_tokens_list):
        path = os.path.join(tmpdir, f"shard_{i:05d}.bin")
        arr = np.array(tokens, dtype=">u2")
        arr.tofile(path)
        paths.append(path)
    return paths


def test_binary_corpus_single_shard():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1 shard with 250 tokens
        tokens = list(range(100, 350))
        create_mock_shards(tmpdir, [tokens])

        cfg = TrainingConfig(seq_len=64)
        ds = BinaryCorpusDataset(cfg, tmpdir)

        # Expected samples: (250 - 64 - 1) // 64 + 1 = 185 // 64 + 1 = 2 + 1 = 3 samples
        # Sample 0: tokens 0..64 (inputs 0..63, targets 1..64)
        # Sample 1: tokens 64..128 (inputs 64..127, targets 65..128)
        # Sample 2: tokens 128..192 (inputs 128..191, targets 129..192)
        assert len(ds) == 3

        inp0, tgt0 = ds[0]
        assert inp0.shape == (64,)
        assert tgt0.shape == (64,)
        assert inp0.dtype == torch.int64
        assert tgt0.dtype == torch.int64
        assert inp0.tolist() == tokens[0:64]
        assert tgt0.tolist() == tokens[1:65]

        inp1, tgt1 = ds[1]
        assert inp1.tolist() == tokens[64:128]
        assert tgt1.tolist() == tokens[65:129]

        ds.close()


def test_binary_corpus_multi_shard_cross_boundary():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Shard 0: 50 tokens (0..49)
        # Shard 1: 50 tokens (50..99)
        # Shard 2: 50 tokens (100..149)
        # Total = 150 tokens
        tokens0 = list(range(0, 50))
        tokens1 = list(range(50, 100))
        tokens2 = list(range(100, 150))
        create_mock_shards(tmpdir, [tokens0, tokens1, tokens2])

        cfg = TrainingConfig(seq_len=64)
        ds = BinaryCorpusDataset(cfg, tmpdir)

        # Total 150. (150 - 65) // 64 + 1 = 85 // 64 + 1 = 2 samples
        # Sample 0: spans shard 0 (50 tok) + shard 1 (first 15 tok)
        # Sample 1: spans shard 1 (tokens 64..99 = 36 tok) + shard 2 (tokens 100..128 = 29 tok)
        assert len(ds) == 2

        inp0, tgt0 = ds[0]
        assert inp0.shape == (64,)
        assert tgt0.shape == (64,)
        all_tokens = tokens0 + tokens1 + tokens2
        assert inp0.tolist() == all_tokens[0:64]
        assert tgt0.tolist() == all_tokens[1:65]

        inp1, tgt1 = ds[1]
        assert inp1.tolist() == all_tokens[64:128]
        assert tgt1.tolist() == all_tokens[65:129]

        ds.close()


def test_binary_corpus_sliding_window_compatibility():
    with tempfile.TemporaryDirectory() as tmpdir:
        tokens = list(range(100))
        create_mock_shards(tmpdir, [tokens])

        cfg = TrainingConfig(seq_len=10)
        ds = BinaryCorpusDataset(cfg, tmpdir, stride=1)

        # Sliding window stride=1: len = 100 - 10 = 90
        assert len(ds) == 90
        inp, tgt = ds[5]
        assert inp.tolist() == tokens[5:15]
        assert tgt.tolist() == tokens[6:16]

        ds.close()
