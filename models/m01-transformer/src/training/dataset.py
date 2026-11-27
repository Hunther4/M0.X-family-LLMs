"""Dataset loaders for training M0.1.

Provides:
- TinyShakespeareDataset: Sliding-window dataset over raw text for baseline smoke tests.
- BinaryCorpusDataset: High-performance dataset over pre-tokenized binary shards (>u2 uint16 big-endian).
"""

import bisect
import os
import numpy as np
import torch
from torch import LongTensor

from src.tokenizer.bpe import Tokenizer
from src.training.config import TrainingConfig


class TinyShakespeareDataset:
    """Sliding-window dataset over raw text corpus (TinyShakespeare / Spanish pretrain).

    Loads the canonical BPE tokenizer from ``data/tokenizers/tokenizer.json``, tokenizes
    text once at init, and provides overlapping ``(input, target)`` pairs of length ``seq_len``
    for autoregressive language model training.
    """

    def __init__(self, config: TrainingConfig) -> None:
        self.seq_len = config.seq_len
        data_dir = config.data_dir

        # All datasets use the single canonical 16K tokenizer.
        tokenizer = Tokenizer()
        tokenizer_path = os.path.join("data", "tokenizers", "tokenizer.json")
        if os.path.exists(tokenizer_path):
            tokenizer.load(tokenizer_path)

        # Check if data_dir is already a path to an existing text file, or check subfolders
        text_path = None
        if os.path.isfile(data_dir):
            text_path = data_dir
        else:
            text_paths = [
                os.path.join(data_dir, "raw_text", "spanish_pretrain.txt"),
                os.path.join(data_dir, "spanish_pretrain.txt"),
                os.path.join(data_dir, "raw_text", "tinyshakespeare.txt"),
                os.path.join(data_dir, "tinyshakespeare.txt"),
                os.path.join(data_dir, "input.txt"),
                os.path.join(data_dir, "tinyshakespeare", "input.txt"),
                os.path.join("data", "tinyshakespeare", "input.txt"),
                os.path.join("data", "raw_text", "spanish_pretrain.txt"),
            ]
            for path in text_paths:
                if os.path.exists(path) and os.path.isfile(path):
                    text_path = path
                    break

        if text_path is not None and os.path.isfile(text_path):
            self.source_files = [text_path]
            with open(text_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        else:
            # Resilient fallback for unit tests without external text files
            self.source_files = ["synthetic_fallback"]
            text = (
                "First Citizen:\nBefore we proceed any further, hear me speak.\n"
                "All:\nSpeak, speak.\n"
                "First Citizen:\nYou are all resolved rather to die than to famish?\n"
                "All:\nResolved. resolved.\n"
            ) * 100

        tokens: list[int] = tokenizer.encode(text)
        if len(tokens) <= self.seq_len:
            # Ensure minimum token length
            tokens = (tokens * (self.seq_len // max(len(tokens), 1) + 2))
        self.tokens: LongTensor = torch.tensor(tokens, dtype=torch.long)

        if len(self.tokens) < self.seq_len:
            raise ValueError(
                f"Corpus length ({len(self.tokens)}) is shorter than sequence "
                f"length ({self.seq_len}). Reduce seq_len or use a larger corpus."
            )

    def __len__(self) -> int:
        """Number of sliding-window samples = total_tokens - seq_len."""
        return max(0, len(self.tokens) - self.seq_len)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Return (input, target) LongTensor pair of shape (seq_len,)."""
        input_ids = self.tokens[idx : idx + self.seq_len]
        target_ids = self.tokens[idx + 1 : idx + self.seq_len + 1]
        return input_ids, target_ids


class BinaryCorpusDataset:
    """Dataset de alto rendimiento sobre shards binarios pre-tokenizados (>u2 uint16 big-endian).

    Características:
    - Chunking por bloques continuos e independientes (stride = seq_len por defecto),
      eliminando redundancia y fuga de datos en train/val.
    - Lectura memmap multi-shard bajo demanda sin cargar arrays completos en memoria RAM.
    - Resolución de fronteras entre shards sin overhead de copia innecesaria.
    - Compatible con torch.utils.data.DataLoader y multiprocessing.
    """

    def __init__(self, config: TrainingConfig, corpus_dir: str, stride: int | None = None, load_to_ram: bool = False) -> None:
        self.seq_len = config.seq_len
        self.corpus_dir = corpus_dir
        # Stride por defecto igual a seq_len para pre-entrenamiento autoregresivo estándar
        self.stride = stride if stride is not None else self.seq_len
        self.load_to_ram = load_to_ram

        shard_files = sorted(
            f for f in os.listdir(corpus_dir)
            if f.startswith("shard_") and f.endswith(".bin")
        )
        if not shard_files:
            raise FileNotFoundError(f"No shard_*.bin found in {corpus_dir}")
        self.source_files = [os.path.join(corpus_dir, fname) for fname in shard_files]

        self._shard_mmaps: list[np.memmap | None] = [None] * len(self.source_files)
        self.shard_token_counts: list[int] = []
        self.shard_cum_tokens: list[int] = [0]

        total_tokens = 0
        for path in self.source_files:
            file_bytes = os.path.getsize(path)
            if file_bytes == 0 or file_bytes % 2 != 0:
                raise ValueError(f"Invalid binary shard {path}: expected non-empty uint16 data")
            n_tok = file_bytes // 2
            self.shard_token_counts.append(n_tok)
            total_tokens += n_tok
            self.shard_cum_tokens.append(total_tokens)

        self.total_tokens = total_tokens
        if self.total_tokens < self.seq_len + 1:
            raise ValueError(
                f"Total tokens ({self.total_tokens}) is less than seq_len + 1 ({self.seq_len + 1})"
            )

        if self.load_to_ram:
            print(f"[BinaryCorpusDataset] Loading {len(self.source_files)} shards ({self.total_tokens:,} tokens, {total_tokens * 2 / 1024**2:.1f} MB) into RAM...")
            self.data = np.empty(self.total_tokens, dtype=">u2")
            offset = 0
            for p, n_tok in zip(self.source_files, self.shard_token_counts):
                with open(p, "rb") as f:
                    f.readinto(self.data[offset : offset + n_tok])
                offset += n_tok
            print("[BinaryCorpusDataset] Corpus successfully pinned in RAM!")
        else:
            self.data = None

    @property
    def shard_mmaps(self) -> list[np.memmap]:
        """Provides backward-compatible list of opened memmaps."""
        return [self._get_mmap(i) for i in range(len(self.source_files))]

    def _get_mmap(self, shard_idx: int) -> np.memmap:
        """Lazily open a memmap for the given shard, safe across processes."""
        if self._shard_mmaps is None or len(self._shard_mmaps) != len(self.source_files):
            self._shard_mmaps = [None] * len(self.source_files)
        mm = self._shard_mmaps[shard_idx]
        if mm is None:
            path = self.source_files[shard_idx]
            n_tok = self.shard_token_counts[shard_idx]
            mm = np.memmap(path, dtype=">u2", mode="r", shape=(n_tok,))
            self._shard_mmaps[shard_idx] = mm
        return mm

    def __len__(self) -> int:
        return max(0, (self.total_tokens - self.seq_len - 1) // self.stride + 1)

    def _read_tokens(self, global_start: int, length: int) -> np.ndarray:
        shard_idx = bisect.bisect_right(self.shard_cum_tokens, global_start) - 1
        local_start = global_start - self.shard_cum_tokens[shard_idx]
        shard_len = self.shard_token_counts[shard_idx]

        curr_mm = self._get_mmap(shard_idx)
        if local_start + length <= shard_len:
            return np.array(curr_mm[local_start : local_start + length], dtype=np.int64)

        out = np.empty(length, dtype=np.int64)
        copied = 0
        while copied < length and shard_idx < len(self.source_files):
            curr_mm = self._get_mmap(shard_idx)
            curr_start = local_start if copied == 0 else 0
            curr_avail = self.shard_token_counts[shard_idx] - curr_start
            to_copy = min(length - copied, curr_avail)
            out[copied : copied + to_copy] = curr_mm[curr_start : curr_start + to_copy]
            copied += to_copy
            shard_idx += 1
            local_start = 0

        return out

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        global_start = idx * self.stride
        if self.data is not None:
            chunk = self.data[global_start : global_start + self.seq_len + 1].astype(np.int64)
        else:
            chunk = self._read_tokens(global_start, self.seq_len + 1)
        input_ids = torch.from_numpy(chunk[:-1])
        target_ids = torch.from_numpy(chunk[1:])
        return input_ids, target_ids

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_shard_mmaps"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._shard_mmaps = [None] * len(self.source_files)

    def close(self) -> None:
        """Cierra explícitamente los descriptores de archivo memmap."""
        if hasattr(self, "_shard_mmaps") and self._shard_mmaps is not None:
            for mm in self._shard_mmaps:
                if mm is not None:
                    try:
                        if hasattr(mm, "_mmap") and mm._mmap is not None:
                            mm._mmap.close()
                    except Exception:
                        pass
            self._shard_mmaps = [None] * len(self.source_files)
        if hasattr(self, "data") and self.data is not None:
            self.data = None

    def __del__(self) -> None:
        self.close()

