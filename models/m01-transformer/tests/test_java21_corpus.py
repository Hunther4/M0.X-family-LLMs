"""Tests for Java 21+ Modern Corpus and Dataset Integration."""

import json
import os
from pathlib import Path
import pytest
import torch

from src.tokenizer.bpe import Tokenizer
from src.training.datasets import JsonlDataset
from src.training.sequence_packing import PackedSequenceIterator

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_FILE = REPO_ROOT / "data" / "corpus_code" / "codigo_java21_moderno_50k_tokens.jsonl"
LEGACY_CORPUS_FILE = REPO_ROOT / "data" / "corpus_code" / "java21_modern.jsonl"
TOKENIZER_FILE = REPO_ROOT / "data" / "tokenizers" / "tokenizer.json"


@pytest.fixture(scope="module")
def tokenizer():
    tok = Tokenizer()
    assert TOKENIZER_FILE.exists(), f"Tokenizer not found at {TOKENIZER_FILE}"
    tok.load(str(TOKENIZER_FILE))
    return tok


def test_java21_corpus_file_exists():
    assert CORPUS_FILE.exists(), f"Corpus file not found: {CORPUS_FILE}"
    assert CORPUS_FILE.stat().st_size > 50_000, "Corpus file is suspiciously small"
    assert LEGACY_CORPUS_FILE.is_symlink(), f"Legacy symlink not found: {LEGACY_CORPUS_FILE}"
    assert LEGACY_CORPUS_FILE.resolve() == CORPUS_FILE.resolve(), "Legacy symlink does not resolve to canonical corpus"


def test_java21_corpus_structure_and_categories():
    required_categories = {
        "virtual_threads",
        "pattern_matching",
        "record_patterns",
        "sequenced_collections",
        "unnamed_patterns",
        "sealed_classes",
        "modern_apis",
    }
    found_categories = set()
    found_types = set()
    total_records = 0

    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            total_records += 1

            assert "system" in data, "Missing 'system' key in record"
            assert "conversation" in data, "Missing 'conversation' key in record"
            assert "<|user|>" in data["conversation"], "Missing <|user|> token"
            assert "<|assistant|>" in data["conversation"], "Missing <|assistant|> token"

            metadata = data.get("metadata", {})
            cat = metadata.get("category")
            if cat:
                found_categories.add(cat)
            t = metadata.get("type")
            if t:
                found_types.add(t)

    assert total_records >= 50, f"Expected at least 50 records, got {total_records}"
    assert required_categories.issubset(found_categories), f"Missing categories: {required_categories - found_categories}"
    assert "architecture_qa" in found_types, "Missing architecture_qa entries"
    assert "code_completion" in found_types, "Missing code_completion entries"


def test_java21_corpus_tokenizer_encoding(tokenizer):
    total_tokens = 0
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            text = f"{data['system']}\n{data['conversation']}"
            tokens = tokenizer.encode(text)
            assert len(tokens) > 100, "Entry too short in tokens"
            total_tokens += len(tokens)

            # Lossless or highly accurate roundtrip
            decoded = tokenizer.decode(tokens)
            assert len(decoded) >= len(text) * 0.95

    assert total_tokens >= 40_000, f"Total tokens should exceed 40,000, got {total_tokens}"


def test_java21_corpus_jsonl_dataset_integration(tokenizer):
    dataset = JsonlDataset(
        tokenizer=tokenizer,
        paths=[str(CORPUS_FILE)],
        seq_len=256,
        max_lines_per_shard=1000,
    )
    assert len(dataset) > 0, "Dataset should have sliding window samples"
    x, y = dataset[0]
    assert x.shape == (256,)
    assert y.shape == (256,)
    assert x.dtype == torch.long
    assert y.dtype == torch.long


def test_java21_corpus_packed_sequence_iterator_integration(tokenizer):
    def doc_token_stream():
        with open(CORPUS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                yield tokenizer.encode(f"{data['system']}\n{data['conversation']}")

    packer = PackedSequenceIterator(doc_token_stream(), seq_len=512, eot_id=256)
    count = 0
    for input_ids, target_ids, attn_mask in packer:
        count += 1
        assert input_ids.shape == (512,)
        assert target_ids.shape == (512,)
        assert attn_mask.shape == (512, 512)
        assert attn_mask.dtype == torch.bool
        if count >= 3:
            break

    assert count >= 3, "Failed to pack at least 3 sequences"
