"""Training Configuration.

This module defines the TrainingConfig dataclass containing all
hyperparameters and paths for the M0.1 training loop.
"""

from dataclasses import dataclass, fields


@dataclass
class TrainingConfig:
    """Configuration for the M0.1 training loop.

    Attributes:
        batch_size: Number of sequences per batch
        seq_len: Maximum sequence length per sample
        max_lr: Peak learning rate
        min_lr_ratio: Minimum LR as fraction of max_lr (cosine decay floor)
        warmup_steps: Number of linear warmup steps
        max_steps: Total training steps
        weight_decay: AdamW weight decay coefficient
        beta1: Adam beta1
        beta2: Adam beta2
        max_norm: Gradient clipping max norm
        log_interval: Steps between console logging
        save_interval: Steps between checkpoint saves
        checkpoint_dir: Directory for model checkpoints
        data_dir: Directory containing training data
    """
    batch_size: int = 4
    seq_len: int = 1024
    max_lr: float = 3e-4
    min_lr_ratio: float = 0.1
    warmup_steps: int = 200
    max_steps: int = 10_000
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    max_norm: float = 1.0
    log_interval: int = 10
    save_interval: int = 500
    val_interval: int = 500
    checkpoint_dir: str = "checkpoints"
    data_dir: str = "data"

    # MoE Runtime Monitoring
    log_moe_metrics: bool = True
    moe_collapse_consecutive_steps: int = 50
    moe_collapse_expert_ratio: float = 0.3
    grad_accum_steps: int = 2
    log_metrics_backend: str = "console"

    # Enterprise SOTA Training Suite
    optimizer: str = "adamw"
    muon_lr: float = 0.02
    scheduler: str = "cosine"
    stable_ratio: float = 0.8

    @classmethod
    def from_yaml(cls, path: str) -> "TrainingConfig":
        """Load config from a YAML file."""
        import yaml
        from pathlib import Path
        with open(Path(path), "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        train_data = data.get("training") or data or {}
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in train_data.items() if k in known}
        return cls(**filtered)

    def to_yaml(self, path: str) -> None:
        """Save config to a YAML file."""
        import yaml
        from pathlib import Path
        data = {"training": {f.name: getattr(self, f.name) for f in fields(self)}}
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(Path(path), "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
