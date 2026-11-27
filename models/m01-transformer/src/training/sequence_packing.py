"""Zero-Waste Sequence Packing for High-Efficiency LLM Pretraining.

Packs multiple variable-length documents into fixed `seq_len` chunks separated by
boundary tokens (<|endoftext|> = EOT_ID = 256), eliminating 100% of wasted padding tokens.

Attention Compatibility:
The yielded attention mask is a block-diagonal causal boolean tensor of shape (seq_len, seq_len).
Arbitrary dense 2D document masks are supported by PyTorch SDPA with backends 'math', 'efficient',
or 'auto'. They are NOT supported by standard Flash Attention (e.g. AOTriton on ROCm), which rejects
explicit masks. When dispatching attention for packed sequences, do NOT force AttentionBackend.FLASH;
use AUTO, EFFICIENT, or MATH.
"""

from __future__ import annotations

import itertools
from collections import deque
from typing import Any, Iterable, Iterator, List, Tuple
import numpy as np
import torch
from torch.utils.data import IterableDataset


class PackedSequenceIterator(IterableDataset):
    """Consumes an iterator of document token IDs and yields exact (input, target, attn_mask) tensors.

    The attention mask is a block-diagonal causal mask of shape (seq_len, seq_len)
    that prevents tokens from attending across document boundaries within a packed
    sequence.

    Attention Compatibility:
    The 2D block-diagonal document mask is compatible with SDPA Math, Efficient, and Auto backends.
    Flash Attention (AOTriton/ROCm) does not support explicit 2D/4D masks; when training with
    PackedSequenceIterator, AttentionDispatcher must use 'auto', 'efficient', or 'math'.
    """

    def __init__(
        self,
        doc_token_iterator: Iterable[List[int]],
        seq_len: int = 1024,
        eot_id: int | Any = 256,
    ) -> None:
        super().__init__()
        self.doc_iter = doc_token_iterator
        self.seq_len = seq_len

        # Configurable eot_id with dynamic extraction from tokenizer instances if provided
        if hasattr(eot_id, "special_tokens") and "<|endoftext|>" in getattr(eot_id, "special_tokens", {}):
            self.eot_id = int(eot_id.special_tokens["<|endoftext|>"])
        elif hasattr(eot_id, "eot_id"):
            self.eot_id = int(eot_id.eot_id)
        elif hasattr(eot_id, "eos_id"):
            self.eot_id = int(eot_id.eos_id)
        elif hasattr(eot_id, "eos_token_id"):
            self.eot_id = int(eot_id.eos_token_id)
        else:
            self.eot_id = int(eot_id)

        self.buffer: deque[int] = deque()
        self._doc_ids: deque[int] = deque()
        self._doc_counter: int = 0

    @staticmethod
    def get_compatible_attention_backends() -> list[str]:
        """Return SDPA backends compatible with dense 2D document attention masks."""
        return ["auto", "efficient", "math"]

    def __iter__(self) -> Iterator[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        # Reset state on every iteration / epoch to prevent residual contamination across passes
        self.buffer = deque()
        self._doc_ids = deque()
        self._doc_counter = 0

        for doc in self.doc_iter:
            if not doc:
                continue
            # Assign a unique document ID and track boundaries
            doc_id = self._doc_counter
            self._doc_counter += 1
            self.buffer.extend(doc)
            self.buffer.append(self.eot_id)
            self._doc_ids.extend([doc_id] * (len(doc) + 1))  # +1 for EOT token

            # Yield chunks of (seq_len + 1) for autoregressive (input, target)
            while len(self.buffer) >= self.seq_len + 1:
                chunk = list(itertools.islice(self.buffer, self.seq_len + 1))
                chunk_doc_ids = list(itertools.islice(self._doc_ids, self.seq_len))

                # Stride = seq_len: pop consumed tokens in O(seq_len) without buffer reallocations
                for _ in range(self.seq_len):
                    self.buffer.popleft()
                    self._doc_ids.popleft()

                chunk_np = np.array(chunk, dtype=np.int64)
                input_ids = torch.from_numpy(chunk_np[:-1])
                target_ids = torch.from_numpy(chunk_np[1:])

                # Build block-diagonal causal attention mask:
                # mask[i, j] = True means position i CAN attend to position j
                doc_tensor = torch.tensor(chunk_doc_ids, dtype=torch.int64)
                same_doc = doc_tensor.unsqueeze(0) == doc_tensor.unsqueeze(1)  # (seq_len, seq_len)
                causal = torch.tril(torch.ones(self.seq_len, self.seq_len, dtype=torch.bool))
                attn_mask = same_doc & causal  # (seq_len, seq_len) bool

                yield input_ids, target_ids, attn_mask
