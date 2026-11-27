"""Enterprise-Grade Optimizers for Large Language Model Pretraining.

Implements:
1. Muon (MomentUm Orthogonalized by Newton-schulz) - SOTA 2D weight matrix optimizer
   used in frontier LLMs (DeepSeek V4, Moonshot Kimi, NanoGPT speedruns).
2. EnterpriseHybridOptimizer - Seamless combination of Muon (for 2D internal linear layers)
   and AdamW (for embeddings, RMSNorms, biases, and router gates).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
from torch.optim import AdamW, Optimizer

try:
    from src.kernel.newton_schulz import zeropower_via_newtonschulz5
except ImportError:
    from kernel.newton_schulz import zeropower_via_newtonschulz5


class Muon(Optimizer):
    """Muon (MomentUm Orthogonalized by Newton-schulz) Optimizer.

    Applies momentum and orthogonalizes updates for 2D hidden layer weight matrices,
    achieving 1.5x-2x faster convergence compared to standard AdamW.
    Supports batched Newton-Schulz execution (grouping tensors by shape) to eliminate
    kernel dispatch bottlenecks on modern accelerators (ROCm/CUDA).

    Args:
        params: Iterable of parameters to optimize.
        lr: Learning rate (default: 0.02 for Muon).
        momentum: Momentum factor (default: 0.95).
        nesterov: Whether to use Nesterov momentum (default: True).
        ns_steps: Number of Newton-Schulz iterations (default: 5).
        weight_decay: Decoupled weight decay coefficient (default: 0.01).
        batched: Whether to batch tensors with identical shape via torch.bmm (default: True).
    """

    def __init__(
        self,
        params,
        lr: float = 0.02,
        momentum: float = 0.95,
        nesterov: bool = True,
        ns_steps: int = 5,
        weight_decay: float = 0.01,
        batched: bool = True,
    ) -> None:
        defaults = dict(
            lr=lr,
            momentum=momentum,
            nesterov=nesterov,
            ns_steps=ns_steps,
            weight_decay=weight_decay,
            batched=batched,
        )
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self, closure=None) -> Optional[float]:
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            lr = group["lr"]
            momentum = group["momentum"]
            nesterov = group["nesterov"]
            ns_steps = group["ns_steps"]
            weight_decay = group["weight_decay"]
            use_batched = group.get("batched", True)

            params_with_grad = [p for p in group["params"] if p.grad is not None]
            if not params_with_grad:
                continue

            for p in params_with_grad:
                if p.grad.is_sparse:
                    raise RuntimeError("Muon does not support sparse gradients")

            if not use_batched:
                # Sequential baseline path
                for p in params_with_grad:
                    g = p.grad
                    state = self.state[p]
                    if len(state) == 0:
                        state["step"] = 0
                        state["momentum_buffer"] = torch.zeros_like(p, memory_format=torch.preserve_format)

                    state["step"] += 1
                    buf = state["momentum_buffer"]

                    # 1. Update momentum buffer
                    buf.mul_(momentum).add_(g, alpha=1.0 - momentum)

                    # 2. Compute effective update direction (Nesterov vs Polyak)
                    if nesterov:
                        update_dir = g.lerp(buf, momentum)
                    else:
                        update_dir = buf

                    # 3. Orthogonalize update direction via Newton-Schulz
                    with torch.profiler.record_function("zeropower_via_newtonschulz5"):
                        if update_dir.ndim >= 2:
                            ns_dtype = torch.bfloat16 if update_dir.is_cuda else torch.float32
                            v = zeropower_via_newtonschulz5(update_dir, steps=ns_steps, compute_dtype=ns_dtype)
                        else:
                            v = update_dir / (update_dir.norm() + 1e-7)

                    # 4. Scale update by RMS-norm of parameter matrix for dimension-invariant step
                    scale = max(1.0, p.size(0) / p.size(1)) ** 0.5 if p.ndim == 2 else 1.0
                    step_size = lr * scale

                    # 5. Weight decay & parameter update
                    if weight_decay > 0.0:
                        p.mul_(1.0 - lr * weight_decay)

                    p.add_(v, alpha=-step_size)
            else:
                # Batched execution: group tensors sharing identical 2D shape
                shape_buckets: Dict[Tuple[int, ...], List[nn.Parameter]] = {}
                others: List[nn.Parameter] = []

                for p in params_with_grad:
                    if p.ndim == 2:
                        shape = tuple(p.shape)
                        if shape not in shape_buckets:
                            shape_buckets[shape] = []
                        shape_buckets[shape].append(p)
                    else:
                        others.append(p)

                # Process each shape group with batched GEMMs (torch.bmm)
                for shape, bucket in shape_buckets.items():
                    M, N = shape
                    dirs = []
                    for p in bucket:
                        g = p.grad
                        state = self.state[p]
                        if len(state) == 0:
                            state["step"] = 0
                            state["momentum_buffer"] = torch.zeros_like(p, memory_format=torch.preserve_format)

                        state["step"] += 1
                        buf = state["momentum_buffer"]
                        buf.mul_(momentum).add_(g, alpha=1.0 - momentum)
                        dirs.append(g.lerp(buf, momentum) if nesterov else buf)

                    scale = max(1.0, M / N) ** 0.5
                    step_size = lr * scale

                    ns_dtype = torch.bfloat16 if dirs[0].is_cuda else torch.float32
                    if len(bucket) == 1:
                        with torch.profiler.record_function("zeropower_via_newtonschulz5"):
                            v = zeropower_via_newtonschulz5(dirs[0], steps=ns_steps, compute_dtype=ns_dtype)
                        p = bucket[0]
                        if weight_decay > 0.0:
                            p.mul_(1.0 - lr * weight_decay)
                        p.add_(v, alpha=-step_size)
                    else:
                        # Stack (K, M, N) for batched Newton-Schulz
                        G_batch = torch.stack(dirs, dim=0)
                        with torch.profiler.record_function("zeropower_via_newtonschulz5"):
                            V_batch = zeropower_via_newtonschulz5(G_batch, steps=ns_steps, compute_dtype=ns_dtype)

                        for i, p in enumerate(bucket):
                            if weight_decay > 0.0:
                                p.mul_(1.0 - lr * weight_decay)
                            p.add_(V_batch[i], alpha=-step_size)

                # Fallback for non-2D parameters (if any)
                for p in others:
                    g = p.grad
                    state = self.state[p]
                    if len(state) == 0:
                        state["step"] = 0
                        state["momentum_buffer"] = torch.zeros_like(p, memory_format=torch.preserve_format)

                    state["step"] += 1
                    buf = state["momentum_buffer"]
                    buf.mul_(momentum).add_(g, alpha=1.0 - momentum)
                    update_dir = g.lerp(buf, momentum) if nesterov else buf

                    with torch.profiler.record_function("zeropower_via_newtonschulz5"):
                        if update_dir.ndim >= 2:
                            v = zeropower_via_newtonschulz5(update_dir, steps=ns_steps)
                        else:
                            v = update_dir / (update_dir.norm() + 1e-7)

                    scale = 1.0
                    step_size = lr * scale
                    if weight_decay > 0.0:
                        p.mul_(1.0 - lr * weight_decay)
                    p.add_(v, alpha=-step_size)

        return loss


class EnterpriseHybridOptimizer(Optimizer):
    """Composite Optimizer running Muon on 2D internal weight matrices and AdamW on the rest.

    - Muon: 2D weights in Attention (Wq, Wk, Wv, Wo) and MLP/MoE expert projections (gate, up, down).
    - AdamW: 1D weights (RMSNorms, biases), Embeddings (`wte`), and Router Gates.
    """

    def __init__(
        self,
        model: nn.Module,
        muon_lr: float = 0.02,
        adamw_lr: float = 3e-4,
        muon_weight_decay: float = 0.01,
        adamw_weight_decay: float = 0.1,
        adamw_betas: Tuple[float, float] = (0.9, 0.95),
        adamw_eps: float = 1e-8,
        use_fused_adamw: bool = True,
        use_batched_muon: bool = True,
    ) -> None:
        self.model = model
        self.muon_params: List[nn.Parameter] = []
        self.adamw_decay_params: List[nn.Parameter] = []
        self.adamw_no_decay_params: List[nn.Parameter] = []

        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue

            is_embedding = "embedding" in name or "wte" in name or "lm_head" in name
            is_router_gate = "router" in name or name.endswith("ff.gate.weight")
            is_1d_or_bias = param.ndim < 2 or "bias" in name or "gamma" in name or "norm" in name

            if param.ndim == 2 and not is_embedding and not is_router_gate and not is_1d_or_bias:
                self.muon_params.append(param)
            elif is_1d_or_bias or is_router_gate:
                self.adamw_no_decay_params.append(param)
            else:
                self.adamw_decay_params.append(param)

        self.muon_opt = Muon(
            self.muon_params,
            lr=muon_lr,
            weight_decay=muon_weight_decay,
            batched=use_batched_muon,
        ) if self.muon_params else None

        adamw_groups = []
        if self.adamw_decay_params:
            adamw_groups.append({"params": self.adamw_decay_params, "weight_decay": adamw_weight_decay, "lr": adamw_lr})
        if self.adamw_no_decay_params:
            adamw_groups.append({"params": self.adamw_no_decay_params, "weight_decay": 0.0, "lr": adamw_lr})

        adamw_params = self.adamw_decay_params + self.adamw_no_decay_params
        all_cuda = (
            torch.cuda.is_available()
            and bool(adamw_params)
            and all(p.is_cuda for p in adamw_params)
        )
        fused = use_fused_adamw and all_cuda and "fused" in AdamW.__init__.__code__.co_varnames
        self.adamw_opt = AdamW(
            adamw_groups,
            lr=adamw_lr,
            betas=adamw_betas,
            eps=adamw_eps,
            fused=fused,
        ) if adamw_groups else None

        combined_groups = []
        if self.muon_opt:
            combined_groups.extend(self.muon_opt.param_groups)
        if self.adamw_opt:
            combined_groups.extend(self.adamw_opt.param_groups)

        defaults = dict(lr=adamw_lr)
        super().__init__(combined_groups, defaults)

    def zero_grad(self, set_to_none: bool = True) -> None:
        if self.muon_opt:
            self.muon_opt.zero_grad(set_to_none=set_to_none)
        if self.adamw_opt:
            self.adamw_opt.zero_grad(set_to_none=set_to_none)

    @torch.no_grad()
    def step(self, closure=None) -> Optional[float]:
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        if self.muon_opt:
            with torch.profiler.record_function("muon_step"):
                self.muon_opt.step()
        if self.adamw_opt:
            with torch.profiler.record_function("adamw_step"):
                self.adamw_opt.step()
        return loss

    def state_dict(self) -> Dict[str, Any]:
        return {
            "muon": self.muon_opt.state_dict() if self.muon_opt else None,
            "adamw": self.adamw_opt.state_dict() if self.adamw_opt else None,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        if "muon" in state_dict and self.muon_opt and state_dict["muon"] is not None:
            self.muon_opt.load_state_dict(state_dict["muon"])
        if "adamw" in state_dict and self.adamw_opt and state_dict["adamw"] is not None:
            self.adamw_opt.load_state_dict(state_dict["adamw"])
        elif "param_groups" in state_dict and self.adamw_opt:
            self.adamw_opt.load_state_dict(state_dict)


__all__ = [
    "zeropower_via_newtonschulz5",
    "Muon",
    "EnterpriseHybridOptimizer",
]
