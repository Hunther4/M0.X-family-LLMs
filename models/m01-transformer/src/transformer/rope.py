"""Backward-compatibility shim. RoPE kernels live in src.kernel.rope."""

try:
    from src.kernel.rope import *
    from src.kernel.rope import __all__
except ImportError:
    from kernel.rope import *
    from kernel.rope import __all__
