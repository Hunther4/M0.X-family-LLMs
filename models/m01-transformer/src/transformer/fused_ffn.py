"""Backward-compatibility shim. SwiGLU / Fused FFN kernels live in src.kernel.swiglu."""

try:
    from src.kernel.swiglu import *
    from src.kernel.swiglu import __all__
except ImportError:
    from kernel.swiglu import *
    from kernel.swiglu import __all__
