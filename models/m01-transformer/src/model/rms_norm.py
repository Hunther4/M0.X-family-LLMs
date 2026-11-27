"""Backward-compatibility shim. RMSNorm lives in src.transformer.rms_norm."""
from src.transformer.rms_norm import RMSNorm  # noqa: F401

__all__ = ["RMSNorm"]
