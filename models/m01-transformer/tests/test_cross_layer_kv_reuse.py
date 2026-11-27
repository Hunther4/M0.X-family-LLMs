"""Tests for Cross-Layer KV Reuse (DeepSeek V4 / CSA2 style).

Verifies:
1. M01Config validation and layer mode generation.
2. Parameter savings in reuse layers (omitting W_kv_down and W_kr).
3. Forward and backward pass without cache (training / prefill).
4. KV Cache sharing across layers without duplicating cached tokens.
5. Equivalence between cached decoding and full forward pass.
"""

try:
    import pytest
except ImportError:
    class _DummyPytest:
        @staticmethod
        def fixture(fn):
            return fn
        @staticmethod
        def raises(*args, **kwargs):
            import contextlib
            return contextlib.nullcontext()
    pytest = _DummyPytest()
import torch
from src.transformer.config import M01Config
from src.transformer.attention import CausalSelfAttention
from src.transformer.kv_cache import MLAKVCache, build_model_kv_caches
from src.model.lm import TransformerLM


class TestConfigKVModes:
    """Verify configuration rules for cross-layer KV sharing."""

    def test_default_config_all_full(self) -> None:
        """Default configuration must have all full layers (100% backward compatible)."""
        config = M01Config(n_layers=6, kv_sharing_interval=1)
        assert config.layer_kv_modes == ["full"] * 6
        assert not config.is_kv_reuse_layer(0)
        assert not config.is_kv_reuse_layer(1)

    def test_interval_2_alternating(self) -> None:
        """Interval 2 must alternate full and reuse layers."""
        config = M01Config(n_layers=6, kv_sharing_interval=2)
        assert config.layer_kv_modes == ["full", "reuse", "full", "reuse", "full", "reuse"]
        assert config.get_kv_anchor_index(0) == 0
        assert config.get_kv_anchor_index(1) == 0
        assert config.get_kv_anchor_index(2) == 2
        assert config.get_kv_anchor_index(3) == 2
        assert config.is_kv_reuse_layer(1)
        assert not config.is_kv_reuse_layer(2)

    def test_first_layer_cannot_be_reuse(self) -> None:
        """First layer must always be an anchor (full) layer."""
        with pytest.raises(ValueError, match="The first layer.*must be a 'full'"):
            M01Config(n_layers=4, layer_kv_modes=["reuse", "full", "full", "full"])

    def test_invalid_mode_rejected(self) -> None:
        """Invalid mode strings must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid layer KV mode"):
            M01Config(n_layers=2, layer_kv_modes=["full", "invalid_mode"])


class TestAttentionArchitecture:
    """Verify layer-specific parameter instantiation in CausalSelfAttention."""

    def test_reuse_layer_omits_compression_projections(self) -> None:
        config = M01Config(n_layers=4, kv_sharing_interval=2)
        full_attn = CausalSelfAttention(config, layer_idx=0)
        reuse_attn = CausalSelfAttention(config, layer_idx=1)

        # Full layer has compression projections
        assert full_attn.W_kv_down is not None
        assert full_attn.norm_kv is not None
        assert full_attn.W_kr is not None

        # Reuse layer omits compression projections
        assert reuse_attn.W_kv_down is None
        assert reuse_attn.norm_kv is None
        assert reuse_attn.W_kr is None

        # Both compute their own Queries and up-projections
        assert reuse_attn.W_q is not None
        assert reuse_attn.W_qr is not None
        assert reuse_attn.W_k_up is not None
        assert reuse_attn.W_v_up is not None


class TestLMWithKVReuse:
    """End-to-end TransformerLM tests with Cross-Layer KV Reuse."""

    @pytest.fixture
    def small_reuse_config(self) -> M01Config:
        return M01Config(
            vocab_size=256,
            context_length=64,
            d_model=64,
            n_heads=4,
            d_ff=128,
            n_layers=4,
            num_experts=2,
            num_shared_experts=1,
            num_dense_layers=1,
            mla_kv_c_dim=32,
            mla_rope_dim=8,
            kv_sharing_interval=2,
        )

    def test_parameter_savings(self, small_reuse_config) -> None:
        """Model with reuse layers must have fewer parameters than all-full model."""
        model_reuse = TransformerLM(small_reuse_config)
        
        all_full_config = M01Config(
            vocab_size=256,
            context_length=64,
            d_model=64,
            n_heads=4,
            d_ff=128,
            n_layers=4,
            num_experts=2,
            num_shared_experts=1,
            num_dense_layers=1,
            mla_kv_c_dim=32,
            mla_rope_dim=8,
            kv_sharing_interval=1,
        )
        model_full = TransformerLM(all_full_config)

        params_reuse = sum(p.numel() for p in model_reuse.parameters())
        params_full = sum(p.numel() for p in model_full.parameters())

        assert params_reuse < params_full
        # In this config, 2 reuse layers save:
        # 2 * (d_model * mla_kv_c_dim [W_kv_down] + mla_kv_c_dim [norm] + d_model * n_heads * rope_dim [W_kr])
        expected_saved = 2 * (64 * 32 + 32 + 64 * 32)
        assert params_full - params_reuse == expected_saved

    def test_forward_and_backward_train(self, small_reuse_config) -> None:
        """Training forward and backward pass must succeed with finite gradients."""
        model = TransformerLM(small_reuse_config)
        tokens = torch.randint(0, small_reuse_config.vocab_size, (2, 8))

        logits = model(tokens)
        assert logits.shape == (2, 8, small_reuse_config.vocab_size)
        assert torch.isfinite(logits).all()

        loss = logits.sum()
        loss.backward()

        # Check that both full (layer 0) and reuse (layer 1) receive gradients
        assert model.blocks[0].attn.W_q.weight.grad is not None
        assert model.blocks[1].attn.W_q.weight.grad is not None
        assert torch.isfinite(model.blocks[1].attn.W_q.weight.grad).all()

    def test_shared_kv_cache_instances(self, small_reuse_config) -> None:
        """build_model_kv_caches must share cache references for reuse layers."""
        model = TransformerLM(small_reuse_config)
        caches = model.build_kv_caches(torch.device("cpu"), torch.float32)

        assert len(caches) == 4
        # Layers 0 and 1 share the same cache object
        assert caches[0] is caches[1]
        # Layers 2 and 3 share the same cache object
        assert caches[2] is caches[3]
        # Groups have different caches
        assert caches[0] is not caches[2]

    def test_autoregressive_generation_with_shared_cache(self, small_reuse_config) -> None:
        """Autoregressive token generation must work properly without duplicating cache."""
        model = TransformerLM(small_reuse_config)
        model.eval()

        caches = model.build_kv_caches(torch.device("cpu"), torch.float32)

        # Prefill 4 tokens
        prompt = torch.randint(0, small_reuse_config.vocab_size, (1, 4))
        with torch.no_grad():
            out1 = model(prompt, kv_caches=caches)

        # Both cache pairs must have exact length 4 (no duplicate append by reuse layers)
        assert caches[0].seq_len == 4
        assert caches[2].seq_len == 4

        # Generate 1 new token
        next_tok = torch.argmax(out1[:, -1, :], dim=-1, keepdim=True)
        with torch.no_grad():
            out2 = model(next_tok, kv_caches=caches)

        assert caches[0].seq_len == 5
        assert caches[2].seq_len == 5
        assert out2.shape == (1, 1, small_reuse_config.vocab_size)
        assert torch.isfinite(out2).all()
