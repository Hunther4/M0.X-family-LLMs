"""DeepSeek-style Mixture of Experts (MoE) Layer.

Implements a Mixture of Experts layer with both shared and routed experts.
- Shared experts capture general common knowledge and are always active.
- Routed experts specialize in different domains and are dynamically gated.

Supports Sqrt(Softplus) scoring function (DeepSeek V4 style) for better gradient flow.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from .config import M01Config
from .feedforward import FeedForward


class MoELayer(nn.Module):
    """DeepSeek-style Mixture of Experts (MoE) Layer.
    
    Combines shared experts (always active) with routed experts (top-k gated).
    Supports Sqrt(Softplus) scoring function (DeepSeek V4 style).
    """
    
    def __init__(self, config: M01Config) -> None:
        """Initialize MoE layer.
        
        Args:
            config: M01Config with num_experts, num_shared_experts, moe_top_k, d_model
        """
        super().__init__()
        
        self.config = config
        self.num_experts = config.num_experts
        self.num_shared_experts = config.num_shared_experts
        self.moe_top_k = config.moe_top_k
        self.capacity_factor = config.capacity_factor
        self._target_capacity_factor = config.capacity_factor
        self.capacity_factor_warmup_steps = config.capacity_factor_warmup_steps
        self.capacity_factor_warmup_start = config.capacity_factor_warmup_start
        self.effective_capacity_factor = self._target_capacity_factor
        
        # Router scoring function: "softmax" (default) or "sqrtsoftplus" (DeepSeek V4)
        self.scoring_func = getattr(config, 'scoring_func', 'softmax')
        self.swiglu_limit = getattr(config, 'swiglu_limit', 10.0)
        
        # Determine internal FFN dimensions for shared and routed experts
        # We partition the routed experts' hidden dimension to keep parameters per token constant.
        d_ff_shared = config.d_ff_shared if config.d_ff_shared is not None else config.d_ff
        d_ff_routed = config.d_ff_routed if config.d_ff_routed is not None else max(1, config.d_ff // max(1, config.moe_top_k))
        
        # Shared experts (optional: skipped when num_shared_experts == 0)
        if self.num_shared_experts > 0:
            self.shared_experts = nn.ModuleList([
                FeedForward(config, d_ff=d_ff_shared, is_routed_expert=False) 
                for _ in range(self.num_shared_experts)
            ])
        
        # Routed experts: Top-k gated (with SwiGLU clamping)
        self.experts = nn.ModuleList([
            FeedForward(config, d_ff=d_ff_routed, is_routed_expert=True) 
            for _ in range(self.num_experts)
        ])
        
        # Gate network to route tokens to routed experts
        self.gate = nn.Linear(config.d_model, config.num_experts, bias=False)

    def set_step(self, step: int) -> None:
        """Update the capacity factor according to the training-step warmup."""
        if step < self.capacity_factor_warmup_steps:
            ratio = step / max(self.capacity_factor_warmup_steps, 1)
            self.effective_capacity_factor = (
                self.capacity_factor_warmup_start
                + (self._target_capacity_factor - self.capacity_factor_warmup_start) * ratio
            )
        else:
            self.effective_capacity_factor = self._target_capacity_factor
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of MoE layer.
        
        Args:
            x: Input tensor of shape (batch, seq_len, d_model)
            
        Returns:
            Output tensor of shape (batch, seq_len, d_model)
        """
        batch_size, seq_len, d_model = x.shape
        x_flat = x.view(-1, d_model)  # (N, d_model)
        
        # 1. Compute shared experts output (optional, skipped when num_shared_experts == 0)
        if self.num_shared_experts > 0:
            shared_out = torch.zeros_like(x_flat)
            for expert in self.shared_experts:
                shared_out += expert(x_flat)
            
        # Initialize default aux loss
        self.current_aux_loss = torch.tensor(0.0, device=x.device, dtype=x.dtype)

        # 2. Handle routed experts
        if self.num_experts <= 1:
            # Fallback if there is only 1 expert
            routed_out = self.experts[0](x_flat)
            output = shared_out + routed_out
            return output.view(batch_size, seq_len, d_model)
            
        # Compute gate logits and probabilities
        gate_logits = self.gate(x_flat)  # (N, num_experts) — CLEAN
        
        if self.scoring_func == "sqrtsoftplus":
            # DeepSeek V4 style: Sqrt(Softplus) scoring for better gradient flow
            # affinity = sqrt(softplus(gate_logits))
            affinity = torch.sqrt(F.softplus(gate_logits))
            clean_probs = F.softmax(affinity.float(), dim=-1).to(gate_logits.dtype)
            routing_probs = clean_probs
        else:
            # Standard softmax scoring (default)
            if self.training:
                # DeepSeek-style gate noise encourages early exploration
                noise_std = 0.1 * F.softplus(gate_logits)
                routing_logits = gate_logits + torch.randn_like(gate_logits) * noise_std
            else:
                routing_logits = gate_logits

            # Clean probabilities are used for losses; noisy probabilities are used
            # only for routing decisions.
            clean_probs = F.softmax(gate_logits.float(), dim=-1).to(gate_logits.dtype)
            routing_probs = F.softmax(routing_logits.float(), dim=-1).to(routing_logits.dtype)
        
        # Select top-k experts
        k = min(self.moe_top_k, self.num_experts)
        topk_probs, topk_indices = torch.topk(routing_probs, k=k, dim=-1)
        
        # Normalize the selected probabilities before capacity filtering. Accepted
        # assignments are normalized again below because capacity may reject ranks.
        topk_probs = topk_probs / topk_probs.sum(dim=-1, keepdim=True).clamp_min(
            torch.finfo(topk_probs.dtype).eps
        )

        # Store routing intermediates (clean values for losses, noisy values for monitoring)
        self.gate_logits = gate_logits
        self.gate_probs = clean_probs
        self.routing_probs = routing_probs
        self.topk_indices = topk_indices
        self.topk_probs = topk_probs
        num_tokens = x_flat.size(0)

        # Limit each routed expert to its capacity. Every Top-K choice is an
        # independent assignment; rejecting one rank does not prevent another
        # rank for the same token from being accepted.
        self.capacity = max(
            1,
            int(num_tokens * k / self.num_experts * self.effective_capacity_factor),
        )
        expert_counts = torch.zeros(
            self.num_experts,
            device=x.device,
            dtype=torch.long,
        )
        accepted_assignments = torch.zeros(
            (num_tokens, k),
            device=x.device,
            dtype=torch.bool,
        )

        for rank in range(k):
            expert_for_token = topk_indices[:, rank]
            weight_for_token = topk_probs[:, rank]
            one_hot = (expert_for_token.clamp(min=0).unsqueeze(-1) == torch.arange(self.num_experts, device=x.device)).float()
            sort_order = torch.argsort(weight_for_token, descending=True)
            one_hot_sorted = one_hot[sort_order]
            cumulative_counts = one_hot_sorted.cumsum(dim=0)
            available = (self.capacity - expert_counts).clamp(min=0).float()
            within_capacity = (cumulative_counts <= available.unsqueeze(0)) & (one_hot_sorted.bool())
            
            inv_sort_order = torch.argsort(sort_order)
            within_capacity_orig = within_capacity[inv_sort_order]
            
            accepted_this_rank = within_capacity_orig.gather(1, expert_for_token.clamp(min=0).unsqueeze(1)).squeeze(1)
            accepted_assignments[:, rank] = accepted_this_rank
            
            accepted_per_expert = within_capacity_orig.sum(dim=0).long()
            expert_counts += accepted_per_expert

        assigned_experts = topk_indices.masked_fill(~accepted_assignments, -1)
        accepted_weights = topk_probs * accepted_assignments.to(topk_probs.dtype)
        accepted_weight_sum = accepted_weights.sum(dim=-1, keepdim=True)
        assigned_weights = torch.where(
            accepted_weight_sum > 0,
            accepted_weights / accepted_weight_sum.clamp_min(torch.finfo(topk_probs.dtype).eps),
            torch.zeros_like(accepted_weights),
        )

        expert_ids = torch.arange(self.num_experts, device=x.device)
        assigned_any = (assigned_experts.unsqueeze(0) == expert_ids.view(-1, 1, 1))
        expert_mask = assigned_any.any(dim=-1).to(x.dtype)

        self.assigned_experts = assigned_experts
        self.assigned_weights = assigned_weights
        self.expert_counts = expert_counts
        self.expert_mask = expert_mask
        self.accepted_assignments_per_rank = accepted_assignments.sum(dim=0)
        self.dropped_tokens = assigned_experts.eq(-1).all(dim=-1).sum()
        
        # 3. Compute auxiliary load balancing loss to prevent routing collapse
        if self.training:
            f = expert_mask.mean(dim=1)  # (num_experts,) post-capacity assignments
            P = clean_probs.mean(dim=0)  # (num_experts,)
            # DeepSeek-style load balancing: num_experts * sum(f * P)
            self.current_aux_loss = self.num_experts * torch.sum(f * P)
        else:
            self.current_aux_loss = torch.tensor(0.0, device=x.device, dtype=x.dtype)

        # Construct dense (num_tokens, num_experts) weight matrix
        token_expert_weights = torch.zeros(
            (num_tokens, self.num_experts),
            device=x.device,
            dtype=x.dtype,
        )
        expert_range = torch.arange(self.num_experts, device=x.device).unsqueeze(0)
        for rank in range(k):
            valid = (assigned_experts[:, rank:rank+1] >= 0)
            is_exp = (assigned_experts[:, rank:rank+1] == expert_range) & valid
            token_expert_weights = token_expert_weights + is_exp.to(x.dtype) * assigned_weights[:, rank:rank+1]

        routed_out = torch.zeros_like(x_flat)
        for i in range(self.num_experts):
            w_i = token_expert_weights[:, i:i+1]
            if w_i.max() == 0:
                continue
            expert_out_i = self.experts[i](x_flat)
            routed_out = routed_out + expert_out_i * w_i
            
        # Combine shared and routed outputs
        output = shared_out + routed_out if self.num_shared_experts > 0 else routed_out

        # Detach monitoring-only routing intermediates to free autograd graph.
        # Tensors needed for loss (gate_logits, gate_probs, assigned_weights, expert_mask)
        # are intentionally kept in the graph.
        self.routing_probs = self.routing_probs.detach()
        self.topk_indices = self.topk_indices.detach()
        self.topk_probs = self.topk_probs.detach()
        self.assigned_experts = self.assigned_experts.detach()
        self.accepted_assignments_per_rank = self.accepted_assignments_per_rank.detach()
        self.dropped_tokens = self.dropped_tokens.detach()
        
        return output.view(batch_size, seq_len, d_model)

    def get_aux_loss(self) -> torch.Tensor:
        """Return the auxiliary load balancing loss (WITHOUT z-loss).

        Z-loss is computed separately via get_z_loss() to avoid double-counting
        when RouterZLossTerm in LossPipeline is also used in the training loop.
        """
        return getattr(self, "current_aux_loss", torch.tensor(0.0, device=self.gate.weight.device))

    def get_z_loss(self) -> torch.Tensor:
        """Return the Router Z-Loss computed during the last forward pass.

        Z-Loss = mean(logsumexp(gate_logits)²) — penalizes large unnormalized gate logits
        to prevent routing collapse (DeepSeek-style).

        Returns zero tensor when not in training mode or when gate_logits are unavailable.
        """
        gate_logits = getattr(self, "gate_logits", None)
        if gate_logits is not None:
            return torch.mean(torch.logsumexp(gate_logits, dim=-1) ** 2)
        return torch.tensor(0.0, device=self.gate.weight.device)
