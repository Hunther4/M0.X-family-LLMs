"""Backward-compatibility shim. Fused Cross-Entropy kernels live in src.kernel.cross_entropy."""

try:
    from src.kernel.cross_entropy import *
    from src.kernel.cross_entropy import __all__
except ImportError:
    from kernel.cross_entropy import *
    from kernel.cross_entropy import __all__
