"""Tests for Packed gate_up_proj FeedForward Network.

Validates:
1. Mathematical equivalence of forward pass and backward gradients between packed gate_up_proj
   and separate gate_proj/up_proj implementations.
2. Backward compatibility for loading legacy checkpoints containing separate gate_proj.weight
   and up_proj.weight keys.
3. Compatibility properties and proxy views for gate_proj and up_proj.
4. Clamping behavior in routed MoE experts with packed GEMM.
"""

import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.transformer.config import M01Config
from src.transformer.feedforward import FeedForward
from src.transformer.fused_ffn import fused_swiglu


class SeparateFeedForward(nn.Module):
    """Reference FeedForward implementation using separate gate_proj and up_proj."""

    def __init__(self, config: M01Config, d_ff: int | None = None, is_routed_expert: bool = False) -> None:
        super().__init__()
        hidden_dim = d_ff if d_ff is not None else config.d_ff
        self.gate_proj = nn.Linear(config.d_model, hidden_dim, bias=False)
        self.up_proj = nn.Linear(config.d_model, hidden_dim, bias=False)
        self.down_proj = nn.Linear(hidden_dim, config.d_model, bias=False)
        self.is_routed_expert = is_routed_expert
        self.swiglu_limit = getattr(config, "swiglu_limit", 10.0) if is_routed_expert else None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate = self.gate_proj(x)
        up = self.up_proj(x)

        if self.is_routed_expert and self.swiglu_limit is not None:
            gate = gate.clamp(max=self.swiglu_limit)
            up = up.clamp(min=-self.swiglu_limit, max=self.swiglu_limit)

        hidden = fused_swiglu(gate, up)
        return self.down_proj(hidden)


def test_packed_vs_separate_equivalence():
    """Validate mathematical equivalence of forward outputs and backward gradients."""
    config = M01Config(d_model=64, n_heads=4, d_ff=128)
    hidden_dim = config.d_ff

    # Use float64 for exact precision verification
    ref = SeparateFeedForward(config).to(dtype=torch.float64)
    packed = FeedForward(config).to(dtype=torch.float64)

    # Copy identical weights from ref to packed
    with torch.no_grad():
        packed.gate_up_proj.weight[:hidden_dim].copy_(ref.gate_proj.weight)
        packed.gate_up_proj.weight[hidden_dim:].copy_(ref.up_proj.weight)
        packed.down_proj.weight.copy_(ref.down_proj.weight)

    torch.manual_seed(42)
    x_ref = torch.randn(2, 8, config.d_model, dtype=torch.float64, requires_grad=True)
    x_packed = x_ref.clone().detach().requires_grad_(True)

    # Forward pass
    out_ref = ref(x_ref)
    out_packed = packed(x_packed)

    torch.testing.assert_close(out_packed, out_ref, rtol=1e-10, atol=1e-10)

    # Backward pass
    target = torch.randn_like(out_ref)
    loss_ref = (out_ref * target).sum()
    loss_packed = (out_packed * target).sum()

    loss_ref.backward()
    loss_packed.backward()

    # Input gradient equivalence
    torch.testing.assert_close(x_packed.grad, x_ref.grad, rtol=1e-10, atol=1e-10)

    # Down projection weight gradient equivalence
    torch.testing.assert_close(packed.down_proj.weight.grad, ref.down_proj.weight.grad, rtol=1e-10, atol=1e-10)

    # Packed weight gradient slices vs separate weight gradients
    torch.testing.assert_close(
        packed.gate_up_proj.weight.grad[:hidden_dim],
        ref.gate_proj.weight.grad,
        rtol=1e-10,
        atol=1e-10,
    )
    torch.testing.assert_close(
        packed.gate_up_proj.weight.grad[hidden_dim:],
        ref.up_proj.weight.grad,
        rtol=1e-10,
        atol=1e-10,
    )

    # Property view gradient equivalence
    torch.testing.assert_close(
        packed.gate_proj.weight.grad,
        ref.gate_proj.weight.grad,
        rtol=1e-10,
        atol=1e-10,
    )
    torch.testing.assert_close(
        packed.up_proj.weight.grad,
        ref.up_proj.weight.grad,
        rtol=1e-10,
        atol=1e-10,
    )


def test_packed_vs_separate_routed_expert_clamping():
    """Validate equivalence with SwiGLU clamping enabled for routed experts."""
    config = M01Config(d_model=32, n_heads=2, d_ff=64, swiglu_limit=5.0)
    hidden_dim = config.d_ff

    ref = SeparateFeedForward(config, is_routed_expert=True).to(dtype=torch.float64)
    packed = FeedForward(config, is_routed_expert=True).to(dtype=torch.float64)

    with torch.no_grad():
        packed.gate_up_proj.weight[:hidden_dim].copy_(ref.gate_proj.weight)
        packed.gate_up_proj.weight[hidden_dim:].copy_(ref.up_proj.weight)
        packed.down_proj.weight.copy_(ref.down_proj.weight)

    # Large values to trigger clamping
    x_ref = (torch.randn(2, 4, config.d_model, dtype=torch.float64) * 10.0).requires_grad_(True)
    x_packed = x_ref.clone().detach().requires_grad_(True)

    out_ref = ref(x_ref)
    out_packed = packed(x_packed)

    torch.testing.assert_close(out_packed, out_ref, rtol=1e-10, atol=1e-10)

    out_ref.sum().backward()
    out_packed.sum().backward()

    torch.testing.assert_close(x_packed.grad, x_ref.grad, rtol=1e-10, atol=1e-10)
    torch.testing.assert_close(
        packed.gate_up_proj.weight.grad[:hidden_dim],
        ref.gate_proj.weight.grad,
        rtol=1e-10,
        atol=1e-10,
    )
    torch.testing.assert_close(
        packed.gate_up_proj.weight.grad[hidden_dim:],
        ref.up_proj.weight.grad,
        rtol=1e-10,
        atol=1e-10,
    )


def test_legacy_state_dict_loading():
    """Validate loading legacy checkpoint containing separate gate_proj and up_proj weights."""
    config = M01Config(d_model=64, n_heads=4, d_ff=128)
    hidden_dim = config.d_ff

    # Generate synthetic legacy state_dict
    legacy_gate = torch.randn(hidden_dim, config.d_model)
    legacy_up = torch.randn(hidden_dim, config.d_model)
    legacy_down = torch.randn(config.d_model, hidden_dim)

    legacy_sd = {
        "gate_proj.weight": legacy_gate.clone(),
        "up_proj.weight": legacy_up.clone(),
        "down_proj.weight": legacy_down.clone(),
    }

    ff = FeedForward(config)
    # Load with strict=True
    incompatible = ff.load_state_dict(legacy_sd, strict=True)
    assert len(incompatible.missing_keys) == 0, f"Unexpected missing keys: {incompatible.missing_keys}"
    assert len(incompatible.unexpected_keys) == 0, f"Unexpected extra keys: {incompatible.unexpected_keys}"

    # Verify weights correctly loaded into packed tensor
    torch.testing.assert_close(ff.gate_up_proj.weight[:hidden_dim], legacy_gate)
    torch.testing.assert_close(ff.gate_up_proj.weight[hidden_dim:], legacy_up)
    torch.testing.assert_close(ff.down_proj.weight, legacy_down)


def test_legacy_nested_state_dict_loading():
    """Validate legacy state_dict loading within a parent module with namespace prefixes."""
    config = M01Config(d_model=32, n_heads=2, d_ff=64)
    hidden_dim = config.d_ff

    class Container(nn.Module):
        def __init__(self, config):
            super().__init__()
            self.layer = nn.ModuleDict({
                "ff": FeedForward(config)
            })

    container = Container(config)

    legacy_gate = torch.randn(hidden_dim, config.d_model)
    legacy_up = torch.randn(hidden_dim, config.d_model)
    legacy_down = torch.randn(config.d_model, hidden_dim)

    legacy_sd = {
        "layer.ff.gate_proj.weight": legacy_gate,
        "layer.ff.up_proj.weight": legacy_up,
        "layer.ff.down_proj.weight": legacy_down,
    }

    incompatible = container.load_state_dict(legacy_sd, strict=True)
    assert len(incompatible.missing_keys) == 0
    assert len(incompatible.unexpected_keys) == 0

    ff = container.layer["ff"]
    torch.testing.assert_close(ff.gate_up_proj.weight[:hidden_dim], legacy_gate)
    torch.testing.assert_close(ff.gate_up_proj.weight[hidden_dim:], legacy_up)
    torch.testing.assert_close(ff.down_proj.weight, legacy_down)


def test_packed_state_dict_roundtrip():
    """Validate standard save and load of packed state_dict."""
    config = M01Config(d_model=32, n_heads=2, d_ff=64)
    ff1 = FeedForward(config)
    sd = ff1.state_dict()

    assert "gate_up_proj.weight" in sd
    assert "down_proj.weight" in sd
    assert "gate_proj.weight" not in sd

    ff2 = FeedForward(config)
    ff2.load_state_dict(sd, strict=True)

    torch.testing.assert_close(ff1.gate_up_proj.weight, ff2.gate_up_proj.weight)
    torch.testing.assert_close(ff1.down_proj.weight, ff2.down_proj.weight)


def test_projection_views_and_properties():
    """Validate gate_proj and up_proj property views, mutation, and callable behavior."""
    config = M01Config(d_model=32, n_heads=2, d_ff=64)
    hidden_dim = config.d_ff
    ff = FeedForward(config)

    # Shape checks
    assert ff.gate_proj.weight.shape == (hidden_dim, config.d_model)
    assert ff.up_proj.weight.shape == (hidden_dim, config.d_model)
    assert ff.gate_proj.in_features == config.d_model
    assert ff.gate_proj.out_features == hidden_dim
    assert ff.up_proj.in_features == config.d_model
    assert ff.up_proj.out_features == hidden_dim

    # Callable check
    x = torch.randn(2, config.d_model)
    out_gate = ff.gate_proj(x)
    expected_gate = F.linear(x, ff.gate_up_proj.weight[:hidden_dim])
    torch.testing.assert_close(out_gate, expected_gate)

    out_up = ff.up_proj(x)
    expected_up = F.linear(x, ff.gate_up_proj.weight[hidden_dim:])
    torch.testing.assert_close(out_up, expected_up)

    # In-place / setter mutation check
    new_gate_w = torch.ones(hidden_dim, config.d_model)
    ff.gate_proj.weight = new_gate_w
    torch.testing.assert_close(ff.gate_up_proj.weight[:hidden_dim], new_gate_w)

    # Parameter count verification: only 2 leaf parameters, total 3 * d_model * hidden_dim
    params = list(ff.parameters())
    assert len(params) == 2
    assert sum(p.numel() for p in params) == 3 * config.d_model * hidden_dim
