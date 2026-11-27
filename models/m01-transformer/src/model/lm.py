"""Transformer Language Model with Weight-Tied Embeddings.

Assembles TokenEmbedding, a stack of TransformerBlock layers, and RMSNorm
into a complete decoder-only language model. The output projection shares
weights with the embedding layer (weight tying), saving ~21M parameters
and providing a single gradient signal through the embedding matrix.
"""

from typing import List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from src.model.block import TransformerBlock
from src.model.rms_norm import RMSNorm
from src.transformer.config import M01Config
from src.transformer.embeddings import TokenEmbedding
from src.transformer.kv_cache import AttentionCache


class TransformerLM(nn.Module):
    """Decoder-only Transformer Language Model.

    Architecture:
        TokenEmbedding → [TransformerBlock × n_layers] → RMSNorm → output_head

    The output head is weight-tied with the embedding layer — no separate
    output projection parameters exist. Accepts optional KV caches for
    efficient autoregressive generation.

    Args:
        config: M01Config with vocab_size, d_model, n_layers, etc.
    """

    def __init__(self, config: M01Config) -> None:
        super().__init__()

        self.config = config
        self.embedding = TokenEmbedding(config)
        self.blocks = nn.ModuleList([
            TransformerBlock(
                config, 
                force_dense=(i < config.num_dense_layers),
                layer_idx=i,
            ) 
            for i in range(config.n_layers)
        ])
        self.norm = RMSNorm(config.d_model)

        # Weight-tied output head: references embedding.weight
        # TokenEmbedding.output_head is a method, not a separate Module
        self.output_head = self.embedding.output_head

    def forward(
        self,
        token_ids: Tensor,
        kv_caches: Optional[List[Optional[AttentionCache]]] = None,
        return_hidden: bool = False,
    ) -> Tensor:
        """Forward pass through the full transformer stack.

        Args:
            token_ids: Token IDs of shape (batch, seq_len)
            kv_caches: Optional list of KV caches, one per layer.
                       Must have length equal to n_layers if provided.
                       Individual entries may be None for layers without cache.
            return_hidden: If True, returns normalized hidden states of shape
                           (batch, seq_len, d_model) without projecting through output_head.

        Returns:
            Logits of shape (batch, seq_len, vocab_size) if return_hidden=False,
            or hidden states of shape (batch, seq_len, d_model) if return_hidden=True.
        """
        # Embed tokens: (batch, seq_len) -> (batch, seq_len, d_model)
        x = self.embedding(token_ids)

        if kv_caches is not None and len(kv_caches) != len(self.blocks):
            raise ValueError(
                f"Expected {len(self.blocks)} KV caches, got {len(kv_caches)}"
            )

        # Pass through each transformer block with Cross-Layer KV Reuse support
        current_shared_kv = None
        for i, block in enumerate(self.blocks):
            cache = kv_caches[i] if kv_caches is not None else None
            x = block(x, kv_cache=cache, shared_kv=current_shared_kv)
            if hasattr(block.attn, "last_shared_kv") and block.attn.kv_mode == "full":
                current_shared_kv = block.attn.last_shared_kv

        # Final normalization
        x = self.norm(x)

        if return_hidden:
            return x

        # Weight-tied output projection: (batch, seq_len, vocab_size)
        return self.output_head(x)

    def forward_hidden(
        self,
        token_ids: Tensor,
        kv_caches: Optional[List[Optional[AttentionCache]]] = None,
    ) -> Tensor:
        """Forward pass returning normalized hidden states directly without output_head.

        Args:
            token_ids: Token IDs of shape (batch, seq_len)
            kv_caches: Optional list of KV caches, one per layer.

        Returns:
            Hidden states of shape (batch, seq_len, d_model)
        """
        return self.forward(token_ids, kv_caches=kv_caches, return_hidden=True)

    def get_embedding_weight(self) -> Tensor:
        """Return the tied embedding weight matrix for chunked loss projection."""
        return self.embedding.embedding.weight

    @property
    def embedding_weight(self) -> Tensor:
        """Property returning the tied embedding weight matrix."""
        return self.embedding.embedding.weight

    def build_kv_caches(
        self, device: torch.device, dtype: Optional[torch.dtype] = None
    ) -> List[AttentionCache]:
        """Build KV caches for all layers, sharing cache instances for reuse layers."""
        from src.transformer.kv_cache import build_model_kv_caches
        return build_model_kv_caches(self.config, device, dtype)

    def get_aux_loss(self) -> Tensor:
        """Collect and average auxiliary losses from all child MoE layers."""
        aux_loss = torch.tensor(0.0, device=self.embedding.embedding.weight.device)
        count = 0
        for block in self.blocks:
            if hasattr(block.ff, "get_aux_loss"):
                aux_loss += block.ff.get_aux_loss()
                count += 1
        return aux_loss / count if count > 0 else aux_loss

    def set_moe_step(self, step: int) -> None:
        """Propagate the training step to every MoE feed-forward layer."""
        for block in self.blocks:
            if hasattr(block.ff, "set_step"):
                block.ff.set_step(step)

    def get_z_loss(self) -> Tensor:
        """Collect and average Router Z-Loss from all child MoE layers."""
        z_loss = torch.tensor(0.0, device=self.embedding.embedding.weight.device)
        count = 0
        for block in self.blocks:
            if hasattr(block.ff, "get_z_loss"):
                z_loss += block.ff.get_z_loss()
                count += 1
        return z_loss / count if count > 0 else z_loss

    def get_moe_metrics(self) -> dict:
        """Compute and return MoE runtime metrics dictionary."""
        from src.training.moe_metrics import compute_moe_metrics
        return compute_moe_metrics(self)

