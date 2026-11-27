"""M0.1 Transformer Configuration.

This module defines the configuration dataclass for the M0.1 transformer model.
All hyperparameters are set with defaults matching docs/architecture.md.
"""

import math
from dataclasses import dataclass, fields

@dataclass
class M01Config:
    """Configuration for the M0.1 decoder-only transformer.
    
    Attributes:
        vocab_size: Vocabulary size (default: 16384)
        context_length: Maximum sequence length (default: 8192)
        d_model: Embedding dimension (default: 640)
        n_heads: Number of attention heads (default: 10)
        d_ff: Feedforward hidden dimension (default: 1728)
        n_layers: Number of transformer layers (default: 12)
        rope_theta: RoPE theta parameter (default: 10000.0)
        num_experts: Number of experts for MoE (default: 1 for dense)
        num_shared_experts: Number of shared experts for DeepSeek-style MoE (default: 0)
        moe_top_k: Number of active routed experts per token (default: 2)
        capacity_factor: Routed-expert capacity headroom over ideal balance (default: 1.25)
        capacity_factor_warmup_steps: Steps to anneal capacity from the warmup start
            to the target capacity factor (default: 2000)
        capacity_factor_warmup_start: Initial routed-expert capacity factor during
            warmup (default: 2.0)
        dropout: Dropout rate (default: 0.0)
    """
    vocab_size: int = 16384
    context_length: int = 65536
    d_model: int = 640
    n_heads: int = 10
    d_ff: int = 1728
    n_layers: int = 12
    rope_theta: float = 10000.0
    # Current MoE: 8 routed + 1 shared + top-2
    num_experts: int = 8
    num_shared_experts: int = 1
    moe_top_k: int = 2
    capacity_factor: float = 1.25
    capacity_factor_warmup_steps: int = 2000
    capacity_factor_warmup_start: float = 2.0
    d_ff_shared: int | None = 448
    d_ff_routed: int | None = 784
    use_hybrid_attention: bool = False
    csa_kv_dim: int = 128
    hca_kv_dim: int = 32
    local_window_size: int = 64
    dropout: float = 0.0
    attention_backend: str = "auto"
    initializer_range: float = 0.02
    scale_residual_projections: bool = True
    
    # SwiGLU clamping for routed experts (DeepSeek V4 style)
    swiglu_limit: float = 10.0
    
    # Router scoring function: "softmax" (default) or "sqrtsoftplus" (DeepSeek V4)
    scoring_func: str = "sqrtsoftplus"

    # MLA (Multi-head Latent Attention) Configuration
    use_mla: bool = True
    mla_kv_c_dim: int = 128
    mla_rope_dim: int = 16  # RoPE dimension per head
    
    # Partial RoPE (p-RoPE): apply rotation to only a fraction of head dimensions
    # Default 0.25 = 25% of dimensions carry positional info (Gemma 4 style)
    partial_rotary_factor: float = 0.25

    # Dense layers layout configuration (number of dense layers before MoE starts)
    num_dense_layers: int = 2

    # Cross-Layer KV Reuse (DeepSeek V4 / CSA2 style)
    # kv_sharing_interval: 1 means standard behavior (each layer is full/anchor).
    # > 1 means anchor layer every N layers, intermediate layers reuse anchor KV.
    kv_sharing_interval: int = 1
    # Optional explicit list of layer modes: e.g. ["full", "reuse", "full", "reuse", ...]
    layer_kv_modes: list[str] | None = None

    # Speculative decoding configuration
    enable_speculative_decoding: bool = False
    speculative_k_tokens: int = 4  # Number of draft tokens to verify
    speculative_draft_layers: int = 4  # Layers in draft model
    speculative_acceptance_threshold: float = 0.8  # Early exit if acceptance < threshold
    speculative_draft_checkpoint: str | None = None  # Path to draft model checkpoint

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.n_layers <= 0:
            raise ValueError("n_layers must be greater than zero")
        if self.initializer_range <= 0:
            raise ValueError("initializer_range must be greater than zero")
        # Ensure d_model is divisible by n_heads
        if self.d_model % self.n_heads != 0:
            raise ValueError(
                f"d_model ({self.d_model}) must be divisible by n_heads ({self.n_heads})"
            )
        if self.attention_backend not in {"auto", "flash", "efficient", "math"}:
            raise ValueError(
                "attention_backend must be one of: auto, flash, efficient, math"
            )
        
        # Compute head dimension
        self.d_head = self.d_model // self.n_heads  # 64 for default config
        
        if self.use_mla:
            # Dynamically clamp mla_rope_dim to be an even number strictly less than d_head
            raw_rope = min(self.mla_rope_dim, max(2, self.d_head - 2))
            self.d_head_rope = raw_rope if raw_rope % 2 == 0 else raw_rope - 1
            self.d_head_no_rope = self.d_head - self.d_head_rope

        # Cross-layer KV reuse validation and assignment
        if self.layer_kv_modes is not None:
            if len(self.layer_kv_modes) != self.n_layers:
                raise ValueError(
                    f"layer_kv_modes length ({len(self.layer_kv_modes)}) must match n_layers ({self.n_layers})"
                )
            if self.layer_kv_modes[0] != "full":
                raise ValueError("The first layer (layer 0) must be a 'full' (anchor) layer")
            for mode in self.layer_kv_modes:
                if mode not in {"full", "reuse"}:
                    raise ValueError(f"Invalid layer KV mode: {mode}. Must be 'full' or 'reuse'")
        else:
            if self.kv_sharing_interval <= 1:
                self.layer_kv_modes = ["full"] * self.n_layers
            else:
                self.layer_kv_modes = [
                    "full" if i % self.kv_sharing_interval == 0 else "reuse"
                    for i in range(self.n_layers)
                ]

    def get_kv_anchor_index(self, layer_idx: int) -> int:
        """Return the index of the anchor layer that supplies KV for layer_idx."""
        if not self.layer_kv_modes or layer_idx >= len(self.layer_kv_modes):
            return layer_idx
        for i in range(layer_idx, -1, -1):
            if self.layer_kv_modes[i] == "full":
                return i
        return 0

    def is_kv_reuse_layer(self, layer_idx: int) -> bool:
        """Check if layer_idx is configured as a reuse layer."""
        if not self.layer_kv_modes or layer_idx >= len(self.layer_kv_modes):
            return False
        return self.layer_kv_modes[layer_idx] == "reuse"

    @property
    def residual_init_std(self) -> float:
        """Initialization std for projections entering the residual stream."""
        if not self.scale_residual_projections:
            return self.initializer_range
        return self.initializer_range / math.sqrt(2.0 * self.n_layers)

    @classmethod
    def from_yaml(cls, path: str) -> "M01Config":
        """Load config from a YAML file. Unknown keys are ignored."""
        import yaml
        from pathlib import Path
        with open(Path(path), "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        model_data = data.get("model", data)
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in model_data.items() if k in known}
        return cls(**filtered)

    def to_yaml(self, path: str) -> None:
        """Save config to a YAML file."""
        import yaml
        from pathlib import Path
        data = {"model": {f.name: getattr(self, f.name) for f in fields(self)}}
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(Path(path), "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
