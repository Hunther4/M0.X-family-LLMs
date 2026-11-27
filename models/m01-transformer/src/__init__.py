import os

# Ensure early AOTriton experimental kernels are enabled on AMD ROCm / RDNA 4 (gfx1200)
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"
