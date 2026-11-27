"""Backward-compatibility shim. RMSNorm kernels live in src.kernel.rms_norm."""

try:
    from src.kernel.rms_norm import *
    from src.kernel.rms_norm import __all__
except ImportError:
    from kernel.rms_norm import *
    from kernel.rms_norm import __all__
