"""Fused SwiGLU Kernel with Triton and PyTorch Autograd Integration.

Hardware-accelerated SwiGLU activation (h = SiLU(g) * u) designed for HPC workloads,
specifically optimized for AMD ROCm / RDNA 4 Wave32 architecture (gfx1200) and NVIDIA CUDA.

Key Architectural Characteristics:
1. Operator Fusion:
   Fuses the gate activation (SiLU) and elementwise multiplication with the up-projection,
   eliminating an intermediate activation write/read cycle to High Bandwidth Memory (HBM).
2. Register-Level Recomputation in Backward Pass:
   Recomputes SiLU(g) and d(SiLU(g))/dg entirely in SRAM registers from saved inputs (g, u),
   bypassing the memory footprint of storing intermediate activation graphs.
3. Numerical Precision:
   Explicit tl.float32 upcasting during arithmetic avoids precision loss and underflow/overflow
   in transcendental functions (tl.exp) when consuming bfloat16 or float16 tensors.
4. RDNA 4 Wave32 Alignment:
   Configured with BLOCK_SIZE=1024 and num_warps=4 (128 threads / workgroup = 4 Wave32 wavefronts)
   to maximize wavefront occupancy and maintain high memory bus utilization.
"""

from typing import Optional, Tuple
import torch
import torch.nn.functional as F

try:
    import triton
    import triton.language as tl
    HAS_TRITON = True
except ImportError:
    triton = None
    tl = None
    HAS_TRITON = False

# Hardware optimization constants for AMD ROCm / RDNA 4 Wave32 (gfx1200)
# 4 warps * 32 threads/wave = 128 threads per block (4 waves per workgroup)
BLOCK_SIZE: int = 1024
NUM_WARPS: int = 4

if HAS_TRITON:
    @triton.jit
    def _swiglu_fwd_kernel(
        GatePtr,
        UpPtr,
        OutPtr,
        n_elements,
        BLOCK_SIZE: tl.constexpr,
    ):
        """Forward Triton kernel computing h = SiLU(g) * u.
        
        Args:
            GatePtr: Pointer to gate tensor in global memory.
            UpPtr: Pointer to up-projection tensor in global memory.
            OutPtr: Pointer to destination output tensor in global memory.
            n_elements: Total number of scalar elements.
            BLOCK_SIZE: Compile-time constant tile size.
        """
        pid = tl.program_id(axis=0).to(tl.int64)
        block_start = pid * BLOCK_SIZE
        offsets = (block_start + tl.arange(0, BLOCK_SIZE)).to(tl.int64)
        mask = offsets < n_elements

        # Explicit upcast to tl.float32 for numerical stability with fp16/bf16
        g = tl.load(GatePtr + offsets, mask=mask, other=0.0).to(tl.float32)
        u = tl.load(UpPtr + offsets, mask=mask, other=0.0).to(tl.float32)

        # SwiGLU: SiLU(g) * u = (g * sigmoid(g)) * u
        # sigmoid(g) = 1.0 / (1.0 + exp(-g))
        sig_g = 1.0 / (1.0 + tl.exp(-g))
        silu_g = g * sig_g
        h = silu_g * u

        # Store result cast to native element type of output tensor
        tl.store(OutPtr + offsets, h.to(OutPtr.dtype.element_ty), mask=mask)

    @triton.jit
    def _swiglu_bwd_kernel(
        DOutPtr,
        GatePtr,
        UpPtr,
        DGatePtr,
        DUpPtr,
        n_elements,
        BLOCK_SIZE: tl.constexpr,
    ):
        """Backward Triton kernel computing du and dg simultaneously in SRAM registers.
        
        Gradient derivations:
            h = silu(g) * u = g * sigmoid(g) * u
            du = dout * silu(g)
            dg = dout * u * d(silu(g))/dg
            where d(silu(g))/dg = sigmoid(g) * (1.0 + g * (1.0 - sigmoid(g)))
            
        Args:
            DOutPtr: Pointer to incoming upstream grad_output in global memory.
            GatePtr: Pointer to forward gate tensor in global memory.
            UpPtr: Pointer to forward up tensor in global memory.
            DGatePtr: Pointer to output gradient tensor w.r.t gate.
            DUpPtr: Pointer to output gradient tensor w.r.t up.
            n_elements: Total number of scalar elements.
            BLOCK_SIZE: Compile-time constant tile size.
        """
        pid = tl.program_id(axis=0).to(tl.int64)
        block_start = pid * BLOCK_SIZE
        offsets = (block_start + tl.arange(0, BLOCK_SIZE)).to(tl.int64)
        mask = offsets < n_elements

        # Load inputs with explicit upcast to tl.float32 for accumulation precision
        dout = tl.load(DOutPtr + offsets, mask=mask, other=0.0).to(tl.float32)
        g = tl.load(GatePtr + offsets, mask=mask, other=0.0).to(tl.float32)
        u = tl.load(UpPtr + offsets, mask=mask, other=0.0).to(tl.float32)

        # Recompute SiLU(g) and dsilu/dg entirely in SRAM registers without HBM traffic
        sig_g = 1.0 / (1.0 + tl.exp(-g))
        silu_g = g * sig_g
        dsilu_dg = sig_g * (1.0 + g * (1.0 - sig_g))

        # Compute du and dg simultaneously
        du = dout * silu_g
        dg = dout * u * dsilu_dg

        # Coalesced write in a single global memory pass, cast to output dtypes
        tl.store(DGatePtr + offsets, dg.to(DGatePtr.dtype.element_ty), mask=mask)
        tl.store(DUpPtr + offsets, du.to(DUpPtr.dtype.element_ty), mask=mask)

else:
    _swiglu_fwd_kernel = None
    _swiglu_bwd_kernel = None


class FusedSwiGLUFunction(torch.autograd.Function):
    """Autograd Function binding Triton SwiGLU kernels with analytical eager fallback."""

    @staticmethod
    def forward(ctx, gate: torch.Tensor, up: torch.Tensor) -> torch.Tensor:
        """Forward pass for SwiGLU activation.
        
        Args:
            gate: Gate tensor [..., d_ff]
            up: Up-projection tensor [..., d_ff]
            
        Returns:
            Activated tensor [..., d_ff]
        """
        if gate.shape != up.shape:
            raise ValueError(
                f"gate and up tensor shapes must match: gate {gate.shape} vs up {up.shape}"
            )
        if gate.dtype != up.dtype:
            raise TypeError(
                f"gate and up tensor dtypes must match: gate {gate.dtype} vs up {up.dtype}"
            )
        if gate.device != up.device:
            raise ValueError(
                f"gate and up devices must match: gate {gate.device} vs up {up.device}"
            )

        if gate.numel() == 0:
            return torch.empty_like(gate)

        orig_shape = gate.shape
        gate_flat = gate.contiguous().view(-1)
        up_flat = up.contiguous().view(-1)
        n_elements = gate_flat.numel()

        use_triton = HAS_TRITON and gate.is_cuda
        ctx.use_triton = use_triton
        ctx.orig_shape = orig_shape
        ctx.save_for_backward(gate_flat, up_flat)

        if use_triton:
            out_flat = torch.empty_like(gate_flat)
            grid = (triton.cdiv(n_elements, BLOCK_SIZE),)
            _swiglu_fwd_kernel[grid](
                gate_flat,
                up_flat,
                out_flat,
                n_elements,
                BLOCK_SIZE=BLOCK_SIZE,
                num_warps=NUM_WARPS,
            )
            return out_flat.view(orig_shape)
        else:
            # Clean PyTorch eager fallback
            out_flat = F.silu(gate_flat) * up_flat
            return out_flat.view(orig_shape)

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Backward pass computing gradients w.r.t gate and up projections.
        
        Args:
            grad_output: Upstream gradient tensor of shape [..., d_ff]
            
        Returns:
            Tuple of (grad_gate, grad_up) matching input shapes and dtypes.
        """
        if grad_output.numel() == 0:
            return torch.empty_like(grad_output), torch.empty_like(grad_output)

        gate_flat, up_flat = ctx.saved_tensors
        orig_shape = ctx.orig_shape

        if grad_output.shape != orig_shape:
            raise ValueError(
                f"grad_output shape {grad_output.shape} does not match forward input shape {orig_shape}"
            )

        grad_out_flat = grad_output.contiguous().view(-1)
        n_elements = grad_out_flat.numel()

        if ctx.use_triton:
            grad_gate_flat = torch.empty_like(gate_flat)
            grad_up_flat = torch.empty_like(up_flat)
            grid = (triton.cdiv(n_elements, BLOCK_SIZE),)
            _swiglu_bwd_kernel[grid](
                grad_out_flat,
                gate_flat,
                up_flat,
                grad_gate_flat,
                grad_up_flat,
                n_elements,
                BLOCK_SIZE=BLOCK_SIZE,
                num_warps=NUM_WARPS,
            )
            return grad_gate_flat.view(orig_shape), grad_up_flat.view(orig_shape)
        else:
            # Clean PyTorch eager fallback with analytical backward
            # Upcast to float32 for numerical stability with fp16/bf16
            g = gate_flat.float()
            u = up_flat.float()
            dout = grad_out_flat.float()

            sig_g = torch.sigmoid(g)
            silu_g = g * sig_g
            dsilu_dg = sig_g * (1.0 + g * (1.0 - sig_g))

            grad_gate = (dout * u * dsilu_dg).to(gate_flat.dtype)
            grad_up = (dout * silu_g).to(up_flat.dtype)

            return grad_gate.view(orig_shape), grad_up.view(orig_shape)


def fused_swiglu(gate: torch.Tensor, up: torch.Tensor) -> torch.Tensor:
    """High-level entry point for Fused SwiGLU activation.
    
    Computes h = SiLU(gate) * up with hardware-accelerated Triton kernels
    on CUDA/ROCm or clean analytical PyTorch eager fallback on CPU.
    
    Args:
        gate: Gate tensor [..., d_ff]
        up: Up-projection tensor [..., d_ff]
        
    Returns:
        Activated tensor [..., d_ff]
    """
    return FusedSwiGLUFunction.apply(gate, up)


__all__ = [
    "fused_swiglu",
    "FusedSwiGLUFunction",
    "BLOCK_SIZE",
    "NUM_WARPS",
    "HAS_TRITON",
]
