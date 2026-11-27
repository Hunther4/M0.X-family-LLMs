"""Backward-compatibility shim. Attention backend dispatcher lives in src.kernel.attention."""

try:
    from src.kernel.attention import *
    from src.kernel.attention import __all__
except ImportError:
    from kernel.attention import *
    from kernel.attention import __all__
