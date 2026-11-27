"""MoE runtime metrics: 20+ metrics across 4 categories.

All metrics are computed from data already stored by MoELayer.forward().
No extra forward passes needed. Each category is a pure function.
"""

import math
from typing import Any, Protocol

import torch
import torch.nn as nn


# ── Distribution Metrics ──────────────────────────────────────────────────────

def expert_usage_histogram(moe: nn.Module, hist: list[int] | None = None) -> list[int]:
    """Token count assigned to each routed expert this step."""
    if hist is not None:
        return hist
    bincount = torch.bincount(moe.topk_indices.flatten(), minlength=moe.num_experts)
    return bincount.tolist()


def tokens_per_expert(moe: nn.Module, hist: list[int] | None = None) -> list[int]:
    """Same as histogram — tokens per expert this step."""
    return expert_usage_histogram(moe, hist=hist)


def expert_utilization_pct(
    moe: nn.Module,
    capacity: int | None = None,
    hist: list[int] | None = None,
) -> list[float]:
    """Utilization % of each expert relative to capacity (if set) or max observed."""
    hist_list = hist if hist is not None else expert_usage_histogram(moe)
    hist_t = torch.tensor(hist_list, dtype=torch.float)
    if capacity is not None and capacity > 0:
        cap = float(capacity)
    else:
        cap = float(hist_t.max().clamp(min=1).item())
    return (hist_t / cap).tolist()


def gini_coefficient(moe: nn.Module, hist: list[int] | None = None) -> float:
    """Gini coefficient for expert token distribution. 0 = perfect balance, 1 = monopoly."""
    hist_list = hist if hist is not None else expert_usage_histogram(moe)
    hist_t = torch.tensor(hist_list, dtype=torch.float)
    if hist_t.sum() <= 0:
        return 0.0
    sorted_h = torch.sort(hist_t)[0]
    n = len(sorted_h)
    cumsum = torch.cumsum(sorted_h, dim=0)
    # Gini = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n+1)/n
    gini = (2.0 * torch.arange(1, n + 1, dtype=torch.float) @ sorted_h) / (n * hist_t.sum()) - (n + 1.0) / n
    return max(0.0, min(1.0, gini.item()))


def imbalance_ratio(moe: nn.Module, hist: list[int] | None = None) -> float:
    """max_usage / min_usage among experts. 1.0 = perfectly balanced."""
    hist_list = hist if hist is not None else expert_usage_histogram(moe)
    hist_t = torch.tensor(hist_list, dtype=torch.float)
    min_val = hist_t[hist_t > 0].min().item() if (hist_t > 0).any() else 1.0
    max_val = hist_t.max().item()
    return max_val / max(min_val, 1.0)


# ── Router Metrics ────────────────────────────────────────────────────────────

def router_entropy(moe: nn.Module, normalize: bool = True) -> float:
    """Mean per-token normalized entropy: 0 = deterministic, 1 = uniform."""
    probs = moe.gate_probs
    n = moe.num_experts
    per_token = -(probs * torch.log(probs.clamp(min=1e-9))).sum(dim=-1)
    mean = float(per_token.mean().item())
    if normalize and n > 1:
        return min(mean / math.log(n), 1.0)
    return mean


def router_confidence(moe: nn.Module) -> float:
    """Mean max probability assigned by router. High = confident routing."""
    return float(moe.gate_probs.max(dim=-1).values.mean().item())


def gate_logits_std(moe: nn.Module) -> float:
    """Std dev of raw gate logits. Growing std = router getting confident."""
    return float(moe.gate_logits.std().item())


def gate_logits_mean(moe: nn.Module) -> float:
    """Mean of raw gate logits."""
    return float(moe.gate_logits.mean().item())


def top1_frequency(moe: nn.Module, num_experts: int | None = None) -> list[float]:
    """Fraction of steps each expert is the #1 choice."""
    n = num_experts if num_experts is not None else moe.num_experts
    top1 = moe.topk_indices[:, 0]  # (N,) — top-1 expert per token
    freq = torch.bincount(top1, minlength=n).float() / max(top1.size(0), 1)
    return freq.tolist()


def top2_frequency(moe: nn.Module, num_experts: int | None = None) -> list[float]:
    """Fraction of steps each expert appears in top-2."""
    n = num_experts if num_experts is not None else moe.num_experts
    if moe.topk_indices.size(-1) < 2:
        return [0.0] * n
    top2 = moe.topk_indices[:, :2].flatten()
    freq = torch.bincount(top2, minlength=n).float() / max(moe.topk_indices.size(0), 1)
    return freq.tolist()


def top4_overlap(moe: nn.Module) -> float:
    """Not meaningful with top_k < 4. Returns 0.0 (current model uses top-2)."""
    return 0.0


# ── Health Metrics ────────────────────────────────────────────────────────────

def dead_expert_info(
    moe: nn.Module,
    num_experts: int | None = None,
    hist: list[int] | None = None,
) -> dict:
    """Which experts received 0 tokens this step."""
    n = num_experts if num_experts is not None else moe.num_experts
    if hist is not None:
        dead_ids = [int(i) for i in range(n) if i < len(hist) and hist[i] == 0]
        return {
            "dead_count": len(dead_ids),
            "dead_ids": dead_ids,
        }
    bincount = torch.bincount(moe.topk_indices.flatten(), minlength=n)
    return {
        "dead_count": int((bincount == 0).sum().item()),
        "dead_ids": [int(i) for i in range(n) if bincount[i].item() == 0],
    }


def expert_saturation(
    moe: nn.Module,
    capacity: int | None = None,
    hist: list[int] | None = None,
) -> list[float]:
    """How close each expert is to capacity. 1.0 = full."""
    hist_list = hist if hist is not None else expert_usage_histogram(moe)
    hist_t = torch.tensor(hist_list, dtype=torch.float)
    if capacity is not None and capacity > 0:
        cap = float(capacity)
    else:
        # Estimate capacity as tokens/experts * top_k
        total = float(hist_t.sum().item())
        cap = max(total / max(moe.num_experts, 1), 1.0)
    return (hist_t / cap).tolist()


def aux_loss_ema(current: float, prev_ema: float, decay: float = 0.99) -> float:
    """Exponential moving average of aux loss."""
    return decay * prev_ema + (1.0 - decay) * current


# ── Quality Metrics (lightweight, no extra forward passes) ────────────────────

def expert_kl_divergence(moe: nn.Module, num_experts: int | None = None) -> float:
    """Mean KL between gate probability distributions (pairwise). O(N^2)."""
    n = num_experts if num_experts is not None else moe.num_experts
    probs = moe.gate_probs  # (N, n)
    # Compute mean distribution per expert (weighted by assignment)
    # Simplified: average gate prob distribution = uniform target
    avg_dist = probs.mean(dim=0)  # (n,)
    uniform = torch.full_like(avg_dist, 1.0 / n)
    kl = (avg_dist * (torch.log(avg_dist + 1e-8) - torch.log(uniform + 1e-8))).sum()
    return float(kl.item())


def shared_expert_usage(moe: nn.Module, num_shared: int | None = None) -> dict:
    """Shared experts are always active for all tokens. Reports count."""
    return {
        "num_shared": num_shared if num_shared is not None else moe.num_shared_experts,
        "active_always": True,
    }


def detect_router_collapse(
    histogram: torch.Tensor | list[int],
    counter: int,
    threshold: int,
    expert_ratio: float = 0.0,
) -> tuple[bool, int]:
    """Detect router collapse based on consecutive under-utilized steps.

    ``expert_ratio`` controls how many experts must be unused before a step is
    considered collapsed. A value of zero preserves the legacy any-dead-expert
    behavior.
    """
    if isinstance(histogram, torch.Tensor):
        dead_ratio = float((histogram == 0).float().mean().item())
    else:
        dead_ratio = sum(count == 0 for count in histogram) / max(len(histogram), 1)
    has_dead = dead_ratio >= expert_ratio if expert_ratio > 0.0 else dead_ratio > 0.0
    if has_dead:
        counter += 1
    else:
        counter = 0
    return counter >= threshold, counter


def check_quick_moe_collapse(
    model: nn.Module,
    expert_ratio: float = 0.8,
) -> bool:
    """Fast check for MoE router collapse across all layers.

    Iterates solely through MoE layers and applies the canonical collapse rule:
    returns True immediately if any layer has dead expert ratio >= expert_ratio
    (default 0.8) or all except <= 1 experts are inactive. Returns False if healthy.
    Avoids computing Gini, KL, entropy, or building the 20+ metrics dict.

    Args:
        model: Model containing MoE layers (e.g. TransformerLM).
        expert_ratio: Ratio threshold for dead experts (defaults to 0.8).

    Returns:
        bool: True if critical router collapse is detected in any layer, False otherwise.
    """
    if hasattr(model, "blocks"):
        for block in model.blocks:
            ff = getattr(block, "ff", None)
            if ff is None or not hasattr(ff, "topk_indices") or ff.topk_indices is None:
                continue
            n_exp = getattr(ff, "num_experts", 1)
            if n_exp <= 1:
                continue

            bincount = torch.bincount(ff.topk_indices.flatten(), minlength=n_exp)
            dead_count = int((bincount == 0).sum().item())
            if dead_count >= n_exp - 1:
                return True
            dead_ratio = dead_count / max(n_exp, 1)
            threshold = expert_ratio if expert_ratio > 0.0 else 0.8
            if dead_ratio >= threshold or (expert_ratio == 0.0 and dead_count > 0):
                return True
        return False

    if hasattr(model, "get_moe_metrics"):
        metrics = model.get_moe_metrics()
        for key, val in metrics.items():
            if not key.endswith("/histogram"):
                continue
            n_exp = len(val)
            if n_exp <= 1:
                continue
            if isinstance(val, torch.Tensor):
                dead_count = int((val == 0).sum().item())
            else:
                dead_count = sum(1 for c in val if c == 0)
            if dead_count >= n_exp - 1:
                return True
            dead_ratio = dead_count / max(n_exp, 1)
            threshold = expert_ratio if expert_ratio > 0.0 else 0.8
            if dead_ratio >= threshold or (expert_ratio == 0.0 and dead_count > 0):
                return True

    return False


def get_quick_moe_histograms(model: nn.Module) -> dict[str, Any]:
    """Retrieve per-layer expert usage histograms without computing telemetry metrics.

    Bypasses calculation of Gini, KL, entropy, confidence, and other telemetry.
    """
    if hasattr(model, "blocks"):
        histograms: dict[str, Any] = {}
        for i, block in enumerate(model.blocks):
            ff = getattr(block, "ff", None)
            if ff is None or not hasattr(ff, "topk_indices") or ff.topk_indices is None:
                continue
            n_exp = getattr(ff, "num_experts", 1)
            if n_exp <= 1:
                continue
            histograms[f"layer_{i}/histogram"] = torch.bincount(
                ff.topk_indices.flatten(), minlength=n_exp
            )
        return histograms

    if hasattr(model, "get_moe_metrics"):
        metrics = model.get_moe_metrics()
        return {k: v for k, v in metrics.items() if k.endswith("/histogram")}

    return {}


# ── Orchestrator ──────────────────────────────────────────────────────────────

def compute_moe_metrics(model: nn.Module) -> dict:
    """Compute ALL MoE metrics from model's MoE layers.

    Collects routing metrics per layer and global aggregates.
    Returns empty dict if no MoE layers with routing data exist.
    """
    # Quick check: no MoE layers or dense-only model
    if not hasattr(model, "blocks") or getattr(getattr(model, "config", None), "num_experts", 1) <= 1:
        return {}

    metrics: dict[str, Any] = {}
    layer_entropies: list[float] = []
    layer_gini: list[float] = []
    layer_dead_counts: list[int] = []
    n_layers_moe = 0

    for i, block in enumerate(model.blocks):
        ff = block.ff
        if not hasattr(ff, "gate_probs"):
            continue
        if not hasattr(ff, "num_experts") or ff.num_experts <= 1:
            continue

        n_layers_moe += 1
        n_exp = ff.num_experts
        prefix = f"layer_{i}"

        # ── Distribution ──
        hist = expert_usage_histogram(ff)
        metrics[f"{prefix}/histogram"] = hist
        metrics[f"{prefix}/gini"] = gini_coefficient(ff, hist=hist)
        metrics[f"{prefix}/imbalance_ratio"] = imbalance_ratio(ff, hist=hist)
        metrics[f"{prefix}/util_pct"] = expert_utilization_pct(ff, hist=hist)

        # ── Router ──
        metrics[f"{prefix}/entropy"] = router_entropy(ff)
        metrics[f"{prefix}/confidence"] = router_confidence(ff)
        metrics[f"{prefix}/gate_logits_std"] = gate_logits_std(ff)
        metrics[f"{prefix}/gate_logits_mean"] = gate_logits_mean(ff)
        metrics[f"{prefix}/top1_freq"] = top1_frequency(ff, n_exp)
        if ff.moe_top_k >= 2:
            metrics[f"{prefix}/top2_freq"] = top2_frequency(ff, n_exp)
        metrics[f"{prefix}/topk"] = ff.moe_top_k

        # ── Health ──
        dead = dead_expert_info(ff, n_exp, hist=hist)
        metrics[f"{prefix}/dead_count"] = dead["dead_count"]
        metrics[f"{prefix}/dead_ids"] = dead["dead_ids"]
        metrics[f"{prefix}/saturation"] = expert_saturation(ff, hist=hist)

        # ── Quality ──
        metrics[f"{prefix}/kl_vs_uniform"] = expert_kl_divergence(ff, n_exp)
        metrics[f"{prefix}/aux_loss"] = ff.get_aux_loss().item()

        # Collect for global aggregates
        layer_entropies.append(metrics[f"{prefix}/entropy"])
        layer_gini.append(metrics[f"{prefix}/gini"])
        layer_dead_counts.append(dead["dead_count"])

    if n_layers_moe == 0:
        return {}

    # ── Global Aggregates ──
    metrics["global/mean_entropy"] = sum(layer_entropies) / n_layers_moe
    metrics["global/mean_gini"] = sum(layer_gini) / n_layers_moe
    metrics["global/total_dead"] = sum(layer_dead_counts)
    metrics["global/n_layers_moe"] = n_layers_moe
    metrics["global/num_experts"] = model.config.num_experts
    metrics["global/moe_top_k"] = model.config.moe_top_k
    metrics["global/num_shared"] = model.config.num_shared_experts
    # Collapse if any MoE layer has dead expert ratio >= 0.8 or all except <= 1 dead
    num_exp = model.config.num_experts
    layer_collapsed = [
        (d >= num_exp - 1 or (d / max(num_exp, 1)) >= 0.8)
        for d in layer_dead_counts
    ]
    metrics["global/router_collapse"] = any(layer_collapsed) if layer_collapsed else False

    return metrics


# ── Protocols ──────────────────────────────────────────────────────────────────

class MetricsLogger(Protocol):
    """Protocol for MoE metric loggers (duck typing).

    Any object with a ``log(metrics, step)`` method satisfies this protocol.
    """

    def log(self, metrics: dict, step: int) -> None: ...


# ── Console Logger ────────────────────────────────────────────────────────────

class ConsoleLogger:
    """Formatted console output of MoE metrics."""

    def log(self, metrics: dict, step: int) -> None:
        if not metrics:
            print(f"\n  MoE Metrics — Step {step}: (no MoE metrics)", flush=True)
            return
        n_moe = metrics.get("global/n_layers_moe", 0)
        if n_moe == 0:
            print(f"\n  MoE Metrics — Step {step}: (no moe layers)", flush=True)
            return

        print(f"\n  MoE Metrics — Step {step}")
        print(f"  Entropy: {metrics.get('global/mean_entropy', 0):.3f}  "
              f"Gini: {metrics.get('global/mean_gini', 0):.3f}  "
              f"Dead: {metrics.get('global/total_dead', 0)}  "
              f"Collapse: {'!' if metrics.get('global/router_collapse', False) else 'OK'}")
        print(end="", flush=True)
