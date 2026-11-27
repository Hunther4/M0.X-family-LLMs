"""Transformer Block with Pre-Norm and Conditional MoE.

Pre-norm transformer block: norm → sublayer → residual.
Supports both dense FeedForward and Mixture of Experts (MoE) based on config.
KV Cache passthrough for autoregressive generation.
"""

from typing import Any, Optional, Tuple, Union
import torch.nn as nn
from torch import Tensor
from src.transformer.config import M01Config
from src.transformer.attention import CausalSelfAttention
from src.transformer.feedforward import FeedForward
from src.transformer.moe import MoELayer
from src.transformer.kv_cache import AttentionCache
from src.transformer.rms_norm import RMSNorm, fused_add_rmsnorm


class TransformerBlock(nn.Module):
    """Pre-norm Transformer block with conditional FF/MoE.

    Applies pre-norm self-attention followed by feedforward (or MoE)
    with residual connections around each sublayer.

    Args:
        config: M01Config with d_model, n_heads, d_ff, num_experts
        force_dense: If True, forces dense FeedForward instead of MoE
        layer_idx: Index of this block in the transformer stack
    """

    def __init__(
        self, 
        config: M01Config, 
        force_dense: bool = False, 
        layer_idx: int = 0
    ) -> None:
        super().__init__()
        self.layer_idx = layer_idx

        # Pre-norm self-attention
        self.norm1 = RMSNorm(config.d_model)
        self.attn = CausalSelfAttention(config, layer_idx=layer_idx)

        # Pre-norm feedforward (dense or MoE)
        self.norm2 = RMSNorm(config.d_model)

        # Dropout applied after attention and FF sublayers
        self.dropout = nn.Dropout(config.dropout)
        if config.num_experts > 1 and not force_dense:
            self.ff = MoELayer(config)
        else:
            self.ff = FeedForward(config)

    def forward(
        self,
        x: Tensor,
        kv_cache: Optional[AttentionCache] = None,
        shared_kv: Optional[Any] = None,
        residual: Optional[Tensor] = None,
        return_residual: bool = False,
    ) -> Union[Tensor, Tuple[Tensor, Tensor]]:
        """Forward pass with pre-norm residual connections.

        Args:
            x: Input tensor of shape (batch, seq_len, d_model)
            kv_cache: Optional KV cache for autoregressive generation
            shared_kv: Optional shared KV tensors from an anchor layer
            residual: Optional incoming residual tensor to fuse with x
            return_residual: If True, returns (hidden, residual) tuple.
                             If False (default), returns single updated tensor.

        Returns:
            Output tensor of shape (batch, seq_len, d_model), or tuple
            (hidden, residual) if return_residual is True.
        """
        # Pre-norm self-attention (fused with residual if provided)
        if residual is not None:
            norm1_out, residual = fused_add_rmsnorm(x, residual, self.norm1.gamma, self.norm1.eps)
        else:
            residual = x
            norm1_out = self.norm1(x)

        attn_out = self.dropout(self.attn(norm1_out, kv_cache=kv_cache, shared_kv=shared_kv))

        # Fused addition of attention residual and RMSNorm for feedforward
        norm2_out, residual = fused_add_rmsnorm(attn_out, residual, self.norm2.gamma, self.norm2.eps)

        ff_out = self.dropout(self.ff(norm2_out))

        if return_residual:
            return ff_out, residual

        # Preserves backward compatibility for callers expecting a single tensor
        return residual + ff_out
