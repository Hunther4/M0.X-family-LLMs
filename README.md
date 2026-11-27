# M0.X-family-LLMs

[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![ROCm](https://img.shields.io/badge/AMD_ROCm-RDNA_4-ED1C24?style=flat-square&logo=amd&logoColor=white)](https://rocm.docs.amd.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](./models/m01-transformer/README.md#license)

**M0.X** es una familia de modelos de lenguaje *decoder-only* de grado de investigación construidos **desde cero en PyTorch**, con enfoque en corpus en español y América Latina (`LatamGPT`). Cada componente —desde Multi-head Latent Attention (MLA) y Mixture of Experts (MoE) estilo DeepSeek hasta los kernels propios y el motor de entrenamiento basado en máquina de estados finitos— está implementado directamente en PyTorch para ofrecer visibilidad completa y control experimental total.

---

## Familia de Modelos

| Variante | Parámetros | Ruteo MoE | Contexto / Vocabulario | Notas |
| :--- | :--- | :--- | :--- | :--- |
| **M0.1 Standard** | ~100M – 160M *(99.7M con 4 expertos ruteados / ~160M con 8 expertos ruteados)* | 8 expertos ruteados + 1 experto compartido, top-2 *(configuración base Enterprise: 4 ruteados + 1 compartido, top-1)* | 32,768 ctx / 16,384 BPE | 12 capas (2 densas SwiGLU + 10 MoE), `d_model=640`, `n_heads=10` |
| **M0.1-Mini** | ~69.6M | 2 expertos ruteados + 1 experto compartido, top-1 | 32,768 ctx / 16,384 BPE | Creado mediante transferencia/fusión de pesos con `scripts/utils/create_m01_mini.py`; **44.13M tokens** acumulados en la corrida alineada con SFT |

---

## Arquitectura e Ingeniería Principal

- **Multi-head Latent Attention (MLA):** Compresión latente de bajo rango para KV (`mla_kv_c_dim=128`, `mla_rope_dim=16`) que reduce la huella de memoria del caché KV en ~77% frente a MHA estándar (288 flotantes/token vs. 1,280 flotantes/token), con RoPE y softmax seguros en FP32.
- **MoE estilo DeepSeek:** Experto compartido siempre activo (`d_ff_shared=448`) junto a expertos ruteados especializados (`d_ff_routed=784`), puntuación de ruteo `sqrtsoftplus`, filtrado por capacidad, pérdida de balanceo de carga, Z-loss y telemetría en vivo de salud MoE (entropía, coeficiente Gini, detección de expertos muertos).
- **Primitivas Modernas de Transformer:** Partial RoPE (**p-RoPE**, `partial_rotary_factor=0.25`), *clamping* de activación SwiGLU (`swiglu_limit=10.0`), *weight tying* entre embeddings de entrada y salida, y `RMSNorm` seguro en FP32.
- **Motor de Entrenamiento V2 (`src/engine_v2/`):** `TrainingEngineV2` orquestado por máquina de estados finitos (`INIT → LOAD → TRAIN ⇄ VALIDATE → SAVE → EVALUATE → EXPORT → FINISHED`) con `EventBus`, `LossPipeline` componible, `AsyncCheckpointManagerV2` (con rollback verificado por SHA256), `EMA`, `AMPContext` (FP16/BF16), `GranularProfiler`, `HealthChecker` (recuperación automática ante NaN/Inf), optimizador Hybrid Muon + AdamW y schedulers WSD / Cosine LR.
- **Kernels Propios (`src/kernel/`):** Implementaciones dedicadas para `attention`, `attention_backend`, `cross_entropy`, `fused_cross_entropy`, `fused_ffn`, `newton_schulz`, `rms_norm`, `rope` y `swiglu`.
- **Caché de Prefijos (`PromptPrefixCache`):** Reutilización acotada por LRU del estado KV para prefijos compartidos de prompt en MLA, Hybrid Attention y MHA, con invalidación automática ante cambios de modelo o configuración.
- **Soporte AMD ROCm / RDNA 4:** Validado en **AMD Radeon RX 9060 XT (16 GB, `gfx1200`, ROCm 6.3 sobre WSL2/Ubuntu)** con kernels AOTriton y ajuste del asignador HIP para WSL2.

---

## Estructura del Repositorio

```text
M0.X-family-LLMs/
├── models/
│   └── m01-transformer/        # Código de M0.1 y M0.1-Mini, src/engine_v2/, src/kernel/, configs/, scripts/, tests/
├── docs/                       # Bitácoras de sesión, hitos de entrenamiento y auditorías energéticas
├── runs/                       # Registros estructurados de corridas (métricas, perfiles, resúmenes; checkpoints ignorados por git)
├── artifacts/                  # Resultados de evaluación y reportes de benchmarks
├── monitoreo_electrico/        # Registros y utilidades de monitoreo eléctrico
├── LEEME_MONITOR_WINDOWS.md    # Documentación del monitor nativo de energía en Go para Windows (power_monitor.exe)
└── README.md                   # Descripción general del repositorio
```

---

## Inicio Rápido

Todos los comandos del modelo, entrenamiento y evaluación se ejecutan desde `models/m01-transformer/`:

```bash
cd models/m01-transformer
```

### 1. Configuración del Entorno

```bash
# PyTorch estándar / CPU o CUDA
pip install -r requirements.txt

# O entorno ROCm bloqueado para GPUs AMD
pip install -r requirements-rocm-lock.txt
```

### 2. Ejecutar Pruebas

```bash
python -m pytest tests/ -q
```

### 3. Crear M0.1-Mini desde M0.1 Standard

Transfiere o fusiona expertos ruteados desde un checkpoint de M0.1 Standard hacia una variante compacta M0.1-Mini sin entrenar desde cero:

```bash
python -m scripts.utils.create_m01_mini --help
```

### 4. Entrenamiento (Preentrenamiento y SFT)

```bash
# Preentrenamiento con TrainingEngineV2 (corpus binario en shards por defecto)
python -m src.training.train --batch-size 4 --max-steps 1000

# Supervised Fine-Tuning (Hybrid Muon + scheduler WSD)
python -m scripts.training.train_sft --optimizer hybrid_muon --scheduler wsd --max-steps 200
```

### 5. Inferencia y Benchmark de Caché de Prefijos

```bash
python -m scripts.evaluation.benchmark_inference \
  --checkpoint checkpoints/checkpoint.pt \
  --tokenizer data/tokenizers/tokenizer.json \
  --prompt "Shared system prompt: first task" \
  --prompt "Shared system prompt: second task" \
  --mode compare \
  --output artifacts/evals/prompt_cache_benchmark.json
```

Para ver la arquitectura en detalle, argumentos CLI y ejemplos de API en Python, consulta [models/m01-transformer/README.md](./models/m01-transformer/README.md).

---

## Telemetría de Energía y Consumo Eléctrico

Este repositorio incluye herramientas de telemetría de hardware y consumo en pared para medir la huella eléctrica y el costo real del entrenamiento local de LLMs:

- **Monitor Nativo de Energía para Windows (`monitoreo_electrico/` y [`LEEME_MONITOR_WINDOWS.md`](./LEEME_MONITOR_WINDOWS.md)):** Binario en Go (`power_monitor.exe`, código fuente en [`models/m01-transformer/scripts/utils/power_monitor_windows.go`](./models/m01-transformer/scripts/utils/power_monitor_windows.go)) que lee el consumo del paquete GPU/CPU desde LibreHardwareMonitor (`http://localhost:8085/data.json`) o utiliza un modelo calibrado para RX 9060 XT (undervolt -75 mV, límite de 130 W) y fuente 80+ Gold con cálculo tarifario CGE Cauquenes BT1 ($265 CLP/kWh).
- **Auditoría Energética de Entrenamiento LatamGPT 20M ([`docs/sesion_2026-11-15_entrenamiento_latamgpt_20m_y_auditoria_energetica.md`](./docs/sesion_2026-11-15_entrenamiento_latamgpt_20m_y_auditoria_energetica.md)):** El preentrenamiento continuo de **M0.1-Mini** durante 2,441 pasos (~14.5 minutos en una RX 9060 XT) consumió **0.073 kWh** (**$19.3 CLP** / ~$0.02 USD), mientras que el undervolt de GPU redujo el consumo total de torre + monitor a ~115–120 W.
