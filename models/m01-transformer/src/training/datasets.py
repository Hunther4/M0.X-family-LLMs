"""Shared dataset classes for M0.1 training scripts.

Provides AmplifiedDialogueDataset for identity/slang/defence SFT training
and JsonlDataset for single or multi-shard JSONL readers used in phase
training scripts.

Window Behavior: All datasets use OVERLAPPING sliding windows
(``__len__ = len(tokens) - seq_len``) to maximize training data from
limited corpora. This matches TinyShakespeareDataset's canonical behavior
and provides better gradient diversity during autoregressive training.
"""

import json
import os
from pathlib import Path

import torch
from torch.utils.data import Dataset


class AmplifiedDialogueDataset(Dataset):
    """Dataset para SFT que tokeniza diálogos con amplificación virtual sin replicar tensores en RAM.

    Args:
        tokenizer: Instancia del Tokenizer.
        dialogues: Lista de diálogos o tuplas (usuario, asistente).
        amp_factor: Número de repeticiones lógicas del dataset.
        seq_len: Longitud de la ventana deslizante.
    """

    def __init__(self, tokenizer, dialogues, amp_factor: int = 1, seq_len: int = 256):
        self.seq_len = seq_len
        self.amp_factor = max(1, int(amp_factor))

        base_tokens = []
        for item in dialogues:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                u_text, a_text = item[0], item[1]
                text = f"<|user|>\n{u_text}\n<|assistant|>\n{a_text}\n"
            else:
                text = f"<|user|>\n{item}\n\n\n"

            tokens = tokenizer.encode(text)
            base_tokens.extend(tokens)

        self.tokens = torch.tensor(base_tokens, dtype=torch.long)
        self.base_len = max(0, len(self.tokens) - self.seq_len)
        print(
            f"AmplifiedDialogueDataset cargado. Tokens base: {len(self.tokens)}, "
            f"Factor: {self.amp_factor}, Longitud efectiva: {len(self)}"
        )

    def __len__(self):
        return self.base_len * self.amp_factor

    def __getitem__(self, idx):
        if self.base_len == 0:
            raise IndexError("Dataset is empty or shorter than seq_len")
        base_idx = idx % self.base_len
        start = base_idx
        end = start + self.seq_len
        return self.tokens[start:end], self.tokens[start + 1 : end + 1]


class JsonlDataset(Dataset):
    """Dataset that reads conversations from one or more JSONL shard files.

    Each JSONL line must contain 'system' and 'conversation' keys. The
    dataset concatenates all tokens from all shards into a single flat
    tensor and provides sliding window chunks.

    Replaces the MultiShardJSONLDataset pattern from training scripts.

    Args:
        tokenizer: Tokenizer instance with an encode() method.
        paths: List of file paths to JSONL shard files.
        seq_len: Sequence length for sliding window chunks (default 256).
        max_lines_per_shard: Maximum lines to read per shard (default 1000).
        eos_token: Optional EOS token ID. If None, derived from tokenizer or fallback.
    """

    def __init__(
        self,
        tokenizer,
        paths,
        seq_len=256,
        max_lines_per_shard=1000,
        eos_token=None,
    ):
        self.seq_len = seq_len
        if eos_token is None:
            eos_token = (
                getattr(tokenizer, "eos_token_id", None)
                or getattr(tokenizer, "special_tokens", {}).get("<|endoftext|>")
                or getattr(tokenizer, "special_tokens", {}).get("<eos>")
                or 256
            )
        self.eos_token = eos_token

        all_tokens = []
        for path in paths:
            if not os.path.exists(path):
                print(f"Warning: Shard {path} not found. Skipping.")
                continue

            cache_file = Path(path).with_suffix(".pt")
            if cache_file.exists() and max_lines_per_shard >= 100_000:
                print(f"Loading pre-tokenized tensor cache from {cache_file}...")
                cached_tokens = torch.load(cache_file, weights_only=True)
                if isinstance(cached_tokens, torch.Tensor):
                    all_tokens.extend(cached_tokens.tolist())
                else:
                    all_tokens.extend(list(cached_tokens))
                continue

            print(f"Tokenizing JSONL data from {path}...")
            with open(path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx >= max_lines_per_shard:
                        break
                    try:
                        data = json.loads(line)
                        if "brief" in data and "report" in data:
                            text = f"<|user|>\n{data['brief']}\n<|assistant|>\n{data['report']}"
                        elif "conversations" in data and isinstance(data["conversations"], list):
                            sys_txt = f"{data['system']}\n" if "system" in data else ""
                            turns = []
                            for turn in data["conversations"]:
                                role = turn.get("role", "user")
                                content = turn.get("content", "")
                                turns.append(f"<|{role}|>\n{content}")
                            text = sys_txt + "\n".join(turns)
                        elif "text" in data or "texto" in data:
                            text = data.get("text") if "text" in data else data.get("texto")
                        elif "code" in data or "codigo" in data:
                            text = data.get("code") if "code" in data else data.get("codigo")
                        elif "system" in data and "conversation" in data:
                            text = f"{data['system']}\n{data['conversation']}"
                        elif "conversation" in data:
                            text = data["conversation"]
                        else:
                            continue

                        tokens = tokenizer.encode(text)
                        all_tokens.extend(tokens)
                        all_tokens.append(self.eos_token)
                    except Exception:
                        continue

        self.tokens = torch.tensor(all_tokens, dtype=torch.long)
        print(
            f"JsonlDataset initialization complete. "
            f"Total tokens in memory: {len(self.tokens)} (EOS: {self.eos_token})"
        )

    def __len__(self):
        """Number of overlapping sliding-window samples."""
        if len(self.tokens) <= self.seq_len:
            return 0
        return len(self.tokens) - self.seq_len

    def __getitem__(self, idx):
        start = idx
        end = start + self.seq_len
        x = self.tokens[start:end]
        y = self.tokens[start + 1 : end + 1]
        return x, y
