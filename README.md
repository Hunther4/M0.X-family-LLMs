# M0.X-family-LLMs

[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![ROCm](https://img.shields.io/badge/AMD_ROCm-RDNA_4-ED1C24?style=flat-square&logo=amd&logoColor=white)](https://rocm.docs.amd.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](./models/m01-transformer/README.md#license)

**M0.X** is a research-grade family of **from-scratch PyTorch decoder-only language models** with a focus on Spanish and Latin American corpora (`LatamGPT`). Every component—from Multi-head Latent Attention (MLA) and DeepSeek-style Mixture of Experts (MoE) to custom kernels and the finite-state-machine training engine—is implemented directly in PyTorch for full architectural visibility and experimental control.

---

## Model Family

| Variant | Parameters | MoE Routing | Context / Vocab | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **M0.1 Standard** | ~100M – 160M *(99.7M @ 4 routed / ~160M @ 8 routed)* | 8 routed experts + 1 shared expert, top-2 *(Enterprise base config: 4 routed + 1 shared, top-1)* | 32,768 ctx / 16,384 BPE | 12 layers (2 dense SwiGLU + 10 MoE), `d_model=640`, `n_heads=10` |
| **M0.1-Mini** | ~69.6M | 2 routed experts + 1 shared expert, top-1 | 32,768 ctx / 16,384 BPE | Created via `scripts/utils/create_m01_mini.py` weight transfer/merge; **44.13M tokens** accumulated in the SFT-aligned run |

---

## Core Architecture & Engineering

- **Multi-head Latent Attention (MLA):** Low-rank KV compression (`mla_kv_c_dim=128`, `mla_rope_dim=16`) reducing KV cache footprint by ~77% compared to standard MHA (288 floats/token vs. 1,280 floats/token), with FP32-safe RoPE and softmax.
- **DeepSeek-style MoE:** Always-active shared expert (`d_ff_shared=448`) paired with specialized routed experts (`d_ff_routed=784`), `sqrtsoftplus` router scoring, capacity filtering, load-balancing loss, Z-loss, and live MoE health telemetry (entropy, Gini coefficient, dead-expert detection).
- **Modern Transformer Primitives:** Partial RoPE (**p-RoPE**, `partial_rotary_factor=0.25`), SwiGLU activation clamping (`swiglu_limit=10.0`), weight-tied input/output embeddings, and FP32-safe `RMSNorm`.
- **V2 Training Engine (`src/engine_v2/`):** FSM-orchestrated `TrainingEngineV2` (`INIT → LOAD → TRAIN ⇄ VALIDATE → SAVE → EVALUATE → EXPORT → FINISHED`) with `EventBus`, composable `LossPipeline`, `AsyncCheckpointManagerV2` (SHA256-verified rollback), `EMA`, `AMPContext` (FP16/BF16), `GranularProfiler`, `HealthChecker` (automatic NaN/Inf recovery), Hybrid Muon + AdamW optimizer, and WSD / Cosine LR schedulers.
- **Custom Kernels (`src/kernel/`):** Dedicated implementations for `attention`, `attention_backend`, `cross_entropy`, `fused_cross_entropy`, `fused_ffn`, `newton_schulz`, `rms_norm`, `rope`, and `swiglu`.
- **Prefix Caching (`PromptPrefixCache`):** Bounded LRU KV-state reuse for shared prompt prefixes across MLA, Hybrid Attention, and MHA, with automatic invalidation on model or config changes.
- **AMD ROCm / RDNA 4 Support:** Validated on **AMD Radeon RX 9060 XT (16 GB, `gfx1200`, ROCm 6.3 on WSL2/Ubuntu)** with AOTriton kernels and WSL2 HIP allocator tuning.

---

## Repository Layout

```text
M0.X-family-LLMs/
├── models/
│   └── m01-transformer/        # M0.1 & M0.1-Mini model code, src/engine_v2/, src/kernel/, configs/, scripts/, tests/
├── docs/                       # Session logs, training milestones, and energy audits
├── runs/                       # Structured training run logs (metrics, profiles, summaries; checkpoints gitignored)
├── artifacts/                  # Evaluation outputs and benchmark reports
├── monitoreo_electrico/        # Power monitoring logs and utilities
├── LEEME_MONITOR_WINDOWS.md    # Documentation for the native Windows Go power monitor (power_monitor.exe)
└── README.md                   # Repository overview
```

---

## Quick Start

All model, training, and evaluation commands run from `models/m01-transformer/`:

```bash
cd models/m01-transformer
```

### 1. Environment Setup

```bash
# Standard PyTorch / CPU or CUDA
pip install -r requirements.txt

# Or use the locked ROCm environment on AMD GPUs
pip install -r requirements-rocm-lock.txt
```

### 2. Run Tests

```bash
python -m pytest tests/ -q
```

### 3. Create M0.1-Mini from M0.1 Standard

Transfer or merge routed experts from an M0.1 Standard checkpoint into a compact M0.1-Mini variant without training from scratch:

```bash
python -m scripts.utils.create_m01_mini --help
```

### 4. Training (Pretraining & SFT)

```bash
# Pretraining with TrainingEngineV2 (default binary shard corpus)
python -m src.training.train --batch-size 4 --max-steps 1000

# Supervised Fine-Tuning (Hybrid Muon + WSD scheduler)
python -m scripts.training.train_sft --optimizer hybrid_muon --scheduler wsd --max-steps 200
```

### 5. Inference & Prefix Cache Benchmarking

```bash
python -m scripts.evaluation.benchmark_inference \
  --checkpoint checkpoints/checkpoint.pt \
  --tokenizer data/tokenizers/tokenizer.json \
  --prompt "Shared system prompt: first task" \
  --prompt "Shared system prompt: second task" \
  --mode compare \
  --output artifacts/evals/prompt_cache_benchmark.json
```

For full architecture details, CLI flags, and Python API examples, see [models/m01-transformer/README.md](./models/m01-transformer/README.md).

---

## Energy & Power Telemetry

This repository includes wall-power and hardware telemetry tooling to measure the real electricity footprint and cost of local LLM training:

- **Native Windows Power Monitor (`monitoreo_electrico/` & [`LEEME_MONITOR_WINDOWS.md`](./LEEME_MONITOR_WINDOWS.md)):** A Go binary (`power_monitor.exe`, source at [`models/m01-transformer/scripts/utils/power_monitor_windows.go`](./models/m01-transformer/scripts/utils/power_monitor_windows.go)) that reads GPU/CPU package power from LibreHardwareMonitor (`http://localhost:8085/data.json`) or falls back to a calibrated RX 9060 XT (-75 mV undervolt, 130 W cap) + 80+ Gold PSU model with CGE Cauquenes BT1 tariff calculation ($265 CLP/kWh).
- **20M-Token LatamGPT Energy Audit ([`docs/sesion_2026-11-15_entrenamiento_latamgpt_20m_y_auditoria_energetica.md`](./docs/sesion_2026-11-15_entrenamiento_latamgpt_20m_y_auditoria_energetica.md)):** Continuous pretraining of **M0.1-Mini** over 2,441 steps (~14.5 minutes on an RX 9060 XT) consumed **0.073 kWh** (**$19.3 CLP** / ~$0.02 USD), while GPU undervolting reduced total workstation + display draw to ~115–120 W.
