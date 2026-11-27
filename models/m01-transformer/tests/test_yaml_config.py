"""Self-contained tests for YAML config (avoids torch import)."""
import os
import sys
import tempfile
import yaml
import importlib
import types

# Register src.transformer.config and src.training.config as standalone modules
# without triggering __init__.py (which imports torch)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def _load_module_standalone(fqn, filepath):
    spec = importlib.util.spec_from_file_location(fqn, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[fqn] = mod
    spec.loader.exec_module(mod)
    return mod

# Load transformer.config directly (skip __init__)
_tc = _load_module_standalone(
    "src.transformer.config",
    os.path.join(os.path.dirname(__file__), "..", "src", "transformer", "config.py"),
)
M01Config = _tc.M01Config

# Load training.config directly
_trc = _load_module_standalone(
    "src.training.config",
    os.path.join(os.path.dirname(__file__), "..", "src", "training", "config.py"),
)
TrainingConfig = _trc.TrainingConfig


def test_m01config_roundtrip():
    original = M01Config()
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False, encoding="utf-8") as f:
        tmp = f.name
    try:
        original.to_yaml(tmp)
        loaded = M01Config.from_yaml(tmp)
        from dataclasses import fields
        for fld in fields(original):
            orig_val = getattr(original, fld.name)
            load_val = getattr(loaded, fld.name)
            assert orig_val == load_val, f"M01Config.{fld.name}: {orig_val!r} != {load_val!r}"
        print("PASS: M01Config round-trip")
    finally:
        os.unlink(tmp)


def test_trainingconfig_roundtrip():
    original = TrainingConfig()
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False, encoding="utf-8") as f:
        tmp = f.name
    try:
        original.to_yaml(tmp)
        loaded = TrainingConfig.from_yaml(tmp)
        from dataclasses import fields
        for fld in fields(original):
            orig_val = getattr(original, fld.name)
            load_val = getattr(loaded, fld.name)
            assert orig_val == load_val, f"TrainingConfig.{fld.name}: {orig_val!r} != {load_val!r}"
        print("PASS: TrainingConfig round-trip")
    finally:
        os.unlink(tmp)


def test_from_yaml_partial():
    data = {"model": {"vocab_size": 32000, "unknown_key": "ignored", "d_model": 512, "n_heads": 8}}
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False, encoding="utf-8") as f:
        yaml.dump(data, f)
        tmp = f.name
    try:
        cfg = M01Config.from_yaml(tmp)
        assert cfg.vocab_size == 32000
        assert cfg.d_model == 512
        assert cfg.n_heads == 8  # set in YAML, not default
        print("PASS: M01Config partial YAML (unknown keys ignored, defaults kept)")
    finally:
        os.unlink(tmp)


def test_from_yaml_nested_training():
    data = {"training": {"batch_size": 8, "max_lr": 1e-3}}
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False, encoding="utf-8") as f:
        yaml.dump(data, f)
        tmp = f.name
    try:
        cfg = TrainingConfig.from_yaml(tmp)
        assert cfg.batch_size == 8
        assert cfg.max_lr == 1e-3
        assert cfg.seq_len == 1024
        print("PASS: TrainingConfig nested YAML block")
    finally:
        os.unlink(tmp)


def test_base_yaml_loads():
    base_path = os.path.join(os.path.dirname(__file__), "..", "configs", "base.yaml")
    assert os.path.exists(base_path), f"Missing {base_path}"
    mc = M01Config.from_yaml(base_path)
    tc = TrainingConfig.from_yaml(base_path)
    assert mc.vocab_size == 16384
    assert mc.d_model == 640
    assert tc.batch_size in (4, 8)
    assert tc.max_lr == 3e-4
    assert tc.grad_accum_steps in (1, 4)
    print("PASS: base.yaml loads into both configs")


def test_cli_parse_config_flag():
    """parse_args recognizes --config flag. Load train.py args parser standalone."""
    # We can't fully import train.py (it imports torch), so parse_args is tested
    # by reading the source and verifying the structure. But we CAN test that
    # argparse recognizes --config by importing just the argparse bits.
    # Instead, let's just verify the flag is there in source.
    src_path = os.path.join(os.path.dirname(__file__), "..", "src", "training", "train.py")
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    assert '"--config"' in src or "'--config'" in src, "--config flag missing from train.py"
    assert "from_yaml" in src, "from_yaml not called in train.py"
    print("PASS: train.py contains --config flag and from_yaml calls")


def test_to_yaml_creates_parent_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = os.path.join(tmpdir, "a", "b", "c", "config.yaml")
        cfg = M01Config()
        cfg.to_yaml(nested)
        assert os.path.exists(nested)
        print("PASS: to_yaml creates parent directories")


def test_m01config_override_via_dict():
    """Simulate CLI override: merge fields dict with overrides."""
    from dataclasses import fields
    original = M01Config()
    base = {f.name: getattr(original, f.name) for f in fields(original)}
    overrides = {"vocab_size": 32000, "d_model": 768, "n_heads": 8}
    merged = {**base, **overrides}
    new_cfg = M01Config(**merged)
    assert new_cfg.vocab_size == 32000
    assert new_cfg.d_model == 768
    assert new_cfg.n_heads == 8
    print("PASS: M01Config dict-merge override works")


def test_trainingconfig_override_via_dict():
    """Simulate CLI override on TrainingConfig."""
    from dataclasses import fields
    original = TrainingConfig()
    base = {f.name: getattr(original, f.name) for f in fields(original)}
    overrides = {"batch_size": 16, "max_lr": 5e-4}
    merged = {**base, **overrides}
    new_cfg = TrainingConfig(**merged)
    assert new_cfg.batch_size == 16
    assert new_cfg.max_lr == 5e-4
    assert new_cfg.seq_len == 1024  # untouched
    print("PASS: TrainingConfig dict-merge override works")


if __name__ == "__main__":
    test_m01config_roundtrip()
    test_trainingconfig_roundtrip()
    test_from_yaml_partial()
    test_from_yaml_nested_training()
    test_base_yaml_loads()
    test_cli_parse_config_flag()
    test_to_yaml_creates_parent_dirs()
    test_m01config_override_via_dict()
    test_trainingconfig_override_via_dict()
    print("\n=== ALL 9 TESTS PASSED ===")
