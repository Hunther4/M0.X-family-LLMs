# M0.X-family-LLMs

Multi-model research repository for the **M0.X** family of from-scratch PyTorch decoder-only language models (MLA + DeepSeek-style MoE), training pipelines, benchmarks, and power-monitoring tooling.

## Repository Structure

- [`models/m01-transformer/`](./models/m01-transformer/) — **M0.1** (Standard ~100M–160M, 8 routed experts) and **M0.1-Mini** (~69.6M, 2 routed experts + 1 shared expert via `scripts/utils/create_m01_mini.py`), including custom ROCm/Triton-style kernels (`src/kernel/`), V2 training engine (`src/engine_v2/`), BPE tokenizer, evaluation scripts, and tests.
- [`docs/`](./docs/) — Session logs, training milestones, and energy audits.
- [`monitoreo_electrico/`](./monitoreo_electrico/) & [`LEEME_MONITOR_WINDOWS.md`](./LEEME_MONITOR_WINDOWS.md) — Windows/Go power telemetry tooling for GPU/wall-power auditing during training.
- [`runs/`](./runs/) & [`artifacts/`](./artifacts/) — Training metrics (`metrics.csv`, `summary.json`, `training_profile.json`) and evaluation results (checkpoints and raw datasets are excluded via `.gitignore`).
