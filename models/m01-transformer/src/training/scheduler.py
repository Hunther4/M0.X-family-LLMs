"""Enterprise Learning Rate Schedulers for LLM Pretraining.

Implements:
1. WSD (Warmup-Stable-Decay) Scheduler - Used by MiniCPM, DeepSeek V2/V3, Llama 3/4.
   - Warmup Phase: Linear increase from 0 to max_lr.
   - Stable Phase: Constant max_lr for 70-85% of total steps (enables continual pretraining).
   - Decay Phase: Cosine or power decay down to min_lr.
2. CosineAnnealingWithWarmup - Classical cosine decay with linear warmup.
"""

from __future__ import annotations

import math
from typing import Callable, Union

from torch.optim import Optimizer
from torch.optim.lr_scheduler import LambdaLR


def get_wsd_schedule(
    optimizer: Optimizer,
    warmup_steps: int,
    max_steps: int,
    stable_ratio: float = 0.8,
    min_lr_ratio: float = 0.1,
    decay_type: str = "cosine",
) -> LambdaLR:
    """Creates a Warmup-Stable-Decay (WSD) schedule.

    Args:
        optimizer: PyTorch or Enterprise optimizer.
        warmup_steps: Number of initial linear warmup steps.
        max_steps: Total number of training steps.
        stable_ratio: Fraction of training steps under warmup + stable phase (e.g. 0.80 = 80%).
        min_lr_ratio: Final minimum LR as a fraction of max_lr (e.g. 0.1 = 10%).
        decay_type: "cosine" or "linear".
    """
    stable_end_step = int(max_steps * stable_ratio)
    if stable_end_step < warmup_steps:
        stable_end_step = warmup_steps
    decay_steps = max(1, max_steps - stable_end_step)

    def lr_lambda(step: int) -> float:
        # Phase 1: Warmup
        if step < warmup_steps:
            return float(step + 1) / float(max(1, warmup_steps))

        # Phase 2: Stable
        if step < stable_end_step:
            return 1.0

        # Phase 3: Decay
        progress = float(step - stable_end_step) / float(decay_steps)
        progress = min(1.0, max(0.0, progress))

        if decay_type == "cosine":
            decay_factor = 0.5 * (1.0 + math.cos(math.pi * progress))
        else:
            decay_factor = 1.0 - progress

        return min_lr_ratio + (1.0 - min_lr_ratio) * decay_factor

    return LambdaLR(optimizer, lr_lambda)


def get_cosine_with_warmup_schedule(
    optimizer: Optimizer,
    warmup_steps: int,
    max_steps: int,
    min_lr_ratio: float = 0.1,
) -> LambdaLR:
    """Classical Cosine decay schedule with linear warmup."""

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step + 1) / float(max(1, warmup_steps))
        progress = float(step - warmup_steps) / float(max(1, max_steps - warmup_steps))
        progress = min(1.0, max(0.0, progress))
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
        return min_lr_ratio + (1.0 - min_lr_ratio) * cosine_decay

    return LambdaLR(optimizer, lr_lambda)
