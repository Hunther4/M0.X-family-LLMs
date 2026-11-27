# Recreate the ROCm environment after cleanup

This repository's retained training artifact is `runs/run_corpus3/checkpoints/checkpoint.pt` (step 19,999). Recreate `venv_rocm` from the lock file after moving or removing the existing environment; do not copy the old virtual environment.

## Quick recreation (Windows PowerShell)

1. Install ROCm **7.14.60850** for the **AMD Radeon RX 9060 XT** and install Python **3.12.10**.
2. From the repository root, create and activate a fresh environment:

   ```powershell
   py -3.12 -m venv venv_rocm
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv_rocm\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   ```

3. Install the ROCm-aware PyTorch bootstrap packages from the same wheel source used for this environment, then install the complete lock:

   ```powershell
   python -m pip install rocm==7.14.0 rocm-bootstrap==0.1.0 rocm-sdk-core==7.14.0 rocm-sdk-device-gfx1200==7.14.0 rocm-sdk-libraries==7.14.0 amd-torch-device-gfx1200==2.12.0+rocm7.14.0 torch==2.12.0+rocm7.14.0
   python -m pip install -r .\requirements-rocm-lock.txt
   ```

4. Verify the recreated environment:

   ```powershell
   python --version
   python -c "import torch, transformers, datasets, accelerate; print(torch.__version__); print(torch.version.hip); print(torch.cuda.get_device_name(0)); print(transformers.__version__, datasets.__version__, accelerate.__version__)"
   ```

Expected values: Python `3.12.10`; torch `2.12.0+rocm7.14.0`; HIP/ROCm `7.14.60850`; `AMD Radeon RX 9060 XT`; transformers `5.14.1`; datasets `5.0.0`; and accelerate `1.14.0`.

## Installation order and fallback

Install ROCm and the ROCm-aware PyTorch packages before the general dependency set. The `torch` wheel must match the ROCm runtime and GPU support package; installing generic dependencies first can cause pip to resolve a different torch build. `requirements-rocm-lock.txt` is the exact `pip freeze --all` snapshot of the current environment. If the bootstrap command is unavailable from the default package source, provide the original ROCm wheel source and install the lock with that same source.

The root `requirements.txt` is intentionally not a reproducibility lock: it contains only six unpinned top-level packages. Use `requirements-rocm-lock.txt` for recovery.

## Cleanup performed

The cleanup was completed after confirming that no project training process was running:

- Retained only `runs/run_corpus3/checkpoints/checkpoint.pt` at step 19,999.
- Removed `checkpoint.previous.pt`, checkpoint checksum sidecars, run logs/metrics, and every other run directory.
- Removed `venv_rocm/`; recreate it at the destination instead of copying it.
- Removed `.pytest_cache` and repository `__pycache__` directories.

Intentionally retained: the step-19,999 `checkpoint.pt` above, this guide, and `requirements-rocm-lock.txt`.

## Do not reuse the old `pyvenv.cfg`

The existing `venv_rocm/pyvenv.cfg` contains stale absolute paths under `D:\Proyectos\M0.1`, including its `executable` and `command` entries, while this checkout is `E:\M0.1`. A virtual environment is location-dependent; create a new one at its destination instead of copying or editing that file.
