"""Feedforward Network with Packed SwiGLU Activation.

Dense SwiGLU feedforward network, MoE-ready via num_experts parameter.
SwiGLU: down(SiLU(gate(x)) ⊙ up(x))

Optimized for AMD ROCm / RDNA 4 Wave32 (gfx1200) and NVIDIA CUDA architectures
by fusing gate_proj and up_proj into a single GEMM projection: gate_up_proj [D, 2F].
Supports SwiGLU clamping for routed experts (DeepSeek V4 style).
Preserves seamless checkpoint compatibility for legacy gate_proj/up_proj weights.
"""

from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from .config import M01Config
from .fused_ffn import fused_swiglu


class _ProjectionWeight(torch.Tensor):
    """Tensor view of a packed linear weight slice that preserves parent gradient linkage."""

    @staticmethod
    def __new__(cls, parent: nn.Parameter, slice_idx: slice):
        tensor_slice = parent[slice_idx]
        obj = torch.Tensor._make_subclass(cls, tensor_slice)
        obj._parent = parent
        obj._slice = slice_idx
        return obj

    @property
    def grad(self) -> Optional[torch.Tensor]:
        if self._parent.grad is None:
            return None
        return self._parent.grad[self._slice]

    @grad.setter
    def grad(self, value: Optional[torch.Tensor]) -> None:
        if value is None:
            if self._parent.grad is not None:
                self._parent.grad[self._slice].zero_()
        else:
            if self._parent.grad is None:
                self._parent.grad = torch.zeros_like(self._parent)
            self._parent.grad[self._slice].copy_(value)


class _ProjectionView(nn.Module):
    """Virtual view of a sliced linear projection (e.g. gate_proj or up_proj).
    
    Provides backward-compatibility for code expecting separate gate_proj/up_proj modules,
    transparently reading from and writing to the underlying packed gate_up_proj.
    """

    def __init__(self, parent_linear: nn.Linear, slice_idx: slice) -> None:
        super().__init__()
        object.__setattr__(self, "_linear", parent_linear)
        object.__setattr__(self, "_slice", slice_idx)

    @property
    def in_features(self) -> int:
        return self._linear.in_features

    @property
    def out_features(self) -> int:
        start = self._slice.start or 0
        stop = self._slice.stop or self._linear.out_features
        return stop - start

    @property
    def weight(self) -> _ProjectionWeight:
        return _ProjectionWeight(self._linear.weight, self._slice)

    @weight.setter
    def weight(self, value: torch.Tensor) -> None:
        with torch.no_grad():
            self._linear.weight[self._slice].copy_(value)

    @property
    def bias(self) -> Optional[_ProjectionWeight]:
        if self._linear.bias is None:
            return None
        return _ProjectionWeight(self._linear.bias, self._slice)

    @bias.setter
    def bias(self, value: Optional[torch.Tensor]) -> None:
        if value is None or self._linear.bias is None:
            return
        with torch.no_grad():
            self._linear.bias[self._slice].copy_(value)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        bias = self._linear.bias[self._slice] if self._linear.bias is not None else None
        return F.linear(x, self._linear.weight[self._slice], bias)

    def extra_repr(self) -> str:
        return f"in_features={self.in_features}, out_features={self.out_features}, bias={self._linear.bias is not None} (packed view)"


class FeedForward(nn.Module):
    """Feedforward network with SwiGLU activation and packed gate_up projection.
    
    When num_experts=1 (default), this is a dense SwiGLU layer.
    When num_experts>1, this can be used as a single expert in MoE.
    Supports optional SwiGLU clamping for routed experts.
    """
    
    def __init__(self, config: M01Config, d_ff: int | None = None, 
                 is_routed_expert: bool = False) -> None:
        """Initialize feedforward network.
        
        Args:
            config: M01Config with d_model, d_ff
            d_ff: Optional override for feedforward hidden dimension
            is_routed_expert: Whether this is a routed expert (enables SwiGLU clamping)
        """
        super().__init__()
        
        hidden_dim = d_ff if d_ff is not None else config.d_ff
        self.hidden_dim = hidden_dim
        
        # Fused gate & up projection [d_model -> 2 * hidden_dim]
        # Halves GEMM launches and maximizes Wave32 arithmetic intensity on AMD ROCm (gfx1200)
        self.gate_up_proj = nn.Linear(config.d_model, 2 * hidden_dim, bias=False)
        self.down_proj = nn.Linear(hidden_dim, config.d_model, bias=False)
        nn.init.normal_(
            self.down_proj.weight,
            mean=0.0,
            std=config.residual_init_std,
        )
        
        # Store config for potential MoE usage
        self.config = config
        
        # SwiGLU clamping for routed experts (DeepSeek V4 style)
        self.is_routed_expert = is_routed_expert
        self.swiglu_limit = getattr(config, 'swiglu_limit', 10.0) if is_routed_expert else None

    @property
    def gate_proj(self) -> _ProjectionView:
        """Backward-compatibility view for gate_proj."""
        return _ProjectionView(self.gate_up_proj, slice(0, self.hidden_dim))

    @property
    def up_proj(self) -> _ProjectionView:
        """Backward-compatibility view for up_proj."""
        return _ProjectionView(self.gate_up_proj, slice(self.hidden_dim, 2 * self.hidden_dim))

    def _load_from_state_dict(
        self, state_dict: dict, prefix: str, local_metadata: dict, strict: bool,
        missing_keys: list, unexpected_keys: list, error_msgs: list
    ) -> None:
        """Handle checkpoint loading compatibility for separated gate_proj and up_proj weights."""
        gate_w_key = f"{prefix}gate_proj.weight"
        up_w_key = f"{prefix}up_proj.weight"
        packed_w_key = f"{prefix}gate_up_proj.weight"

        if gate_w_key in state_dict and up_w_key in state_dict and packed_w_key not in state_dict:
            gate_w = state_dict.pop(gate_w_key)
            up_w = state_dict.pop(up_w_key)
            state_dict[packed_w_key] = torch.cat([gate_w, up_w], dim=0)

        gate_b_key = f"{prefix}gate_proj.bias"
        up_b_key = f"{prefix}up_proj.bias"
        packed_b_key = f"{prefix}gate_up_proj.bias"

        if gate_b_key in state_dict and up_b_key in state_dict and packed_b_key not in state_dict:
            gate_b = state_dict.pop(gate_b_key)
            up_b = state_dict.pop(up_b_key)
            state_dict[packed_b_key] = torch.cat([gate_b, up_b], dim=0)

        super()._load_from_state_dict(
            state_dict, prefix, local_metadata, strict,
            missing_keys, unexpected_keys, error_msgs
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with packed SwiGLU activation.
        
        Args:
            x: Input tensor of shape (batch, seq_len, d_model)
            
        Returns:
            Output tensor of shape (batch, seq_len, d_model)
        """
        # Single fused GEMM for gate and up projections: [B, S, D] -> [B, S, 2F]
        gate_up = self.gate_up_proj(x)
        gate, up = gate_up.chunk(2, dim=-1)
        
        # Apply SwiGLU clamping for routed experts (DeepSeek V4 style)
        if self.is_routed_expert and self.swiglu_limit is not None:
            gate = gate.clamp(max=self.swiglu_limit)
            up = up.clamp(min=-self.swiglu_limit, max=self.swiglu_limit)
        
        # Hardware-accelerated SwiGLU activation: SiLU(gate) * up
        hidden = fused_swiglu(gate, up)
        
        # Down projection
        output = self.down_proj(hidden)
        
        return output
