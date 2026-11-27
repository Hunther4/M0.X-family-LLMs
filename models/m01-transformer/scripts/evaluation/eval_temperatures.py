"""Batería de Pruebas Progresivas por Temperaturas para M0.1 (Checkpoint 5778 pasos).

Evalúa:
- Temperaturas: 0.1 (Muy enfocado), 0.3 (Equilibrado), 0.7 (Creativo/Exploratorio).
- Dificultades:
  1. Suave: Identidad, saludos, definiciones directas.
  2. Intermedio: Explicaciones de código, SOLID, lógica básica.
  3. Avanzado: Razonamiento matemático multipaso, algoritmos, arquitectura de software.
"""

import os
import sys
import torch

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.tokenizer.bpe import Tokenizer
from src.inference.generate import generate
from src.engine_v2.checkpoint_v2 import safe_load_checkpoint, normalize_checkpoint_state

CHECKPOINT_PATH = "runs/run_sft_1m_b8/checkpoints/checkpoint.pt"

TEST_SUITE = [
    # --- NIVEL 1: SUAVE (Identidad y Fundamentos) ---
    {
        "nivel": "1. SUAVE",
        "prompt": "¿Quién eres y cuál es tu arquitectura de modelo?",
        "temperaturas": [0.1, 0.3]
    },
    {
        "nivel": "1. SUAVE",
        "prompt": "<|user|>\nHola M0.1, ¿qué puedes hacer por mí?\n<|assistant|>\n",
        "temperaturas": [0.2]
    },

    # --- NIVEL 2: INTERMEDIO (Código Python, Lógica y SOLID) ---
    {
        "nivel": "2. INTERMEDIO",
        "prompt": "Explica el principio de Inversión de Dependencias (D en SOLID) con un ejemplo corto en Python.",
        "temperaturas": [0.2, 0.4]
    },
    {
        "nivel": "2. INTERMEDIO",
        "prompt": "¿Para qué sirve el parámetro drop_last=True en un DataLoader de PyTorch?",
        "temperaturas": [0.2, 0.5]
    },

    # --- NIVEL 3: AVANZADO (Razonamiento Lógico, Matemáticas y Arquitectura) ---
    {
        "nivel": "3. AVANZADO",
        "prompt": "Resuelve paso a paso: Si un servidor procesa 120 peticiones por minuto y la latencia promedio es 50ms, ¿cuántas peticiones procesa en 3.5 horas?",
        "temperaturas": [0.1, 0.3, 0.6]
    },
    {
        "nivel": "3. AVANZADO",
        "prompt": "Explica la diferencia técnica entre Mixture of Experts (MoE) y Dense Transformers, detallando el ruteo de tokens.",
        "temperaturas": [0.2, 0.5]
    }
]


def run_benchmark():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[BENCHMARK] Dispositivo: {device}")
    print(f"[BENCHMARK] Cargar Checkpoint 5778 pasos desde: {CHECKPOINT_PATH}")

    state = safe_load_checkpoint(CHECKPOINT_PATH, map_location=device)
    state = normalize_checkpoint_state(state, require_architecture=True)
    config_dict = state["model_config"]
    valid_fields = set(M01Config.__dataclass_fields__)
    config = M01Config(**{k: v for k, v in config_dict.items() if k in valid_fields})

    model = TransformerLM(config).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()

    tokenizer = Tokenizer()
    tok_json = os.path.join("data", "tokenizers", "tokenizer.json")
    if os.path.exists(tok_json):
        tokenizer.load(tok_json)

    print("\n" + "=" * 80)
    print("      M0.1 — BENCHMARK DE TEMPERATURAS Y NIVELES DE RAZONAMIENTO (5778 PASOS)")
    print("=" * 80 + "\n")

    for i, test in enumerate(TEST_SUITE, 1):
        print(f"==========================================================")
        print(f" PRUEBA #{i} | {test['nivel']}")
        print(f" PROMPT: {test['prompt']}")
        print(f"==========================================================")

        for temp in test["temperaturas"]:
            print(f"\n[Temperatura: {temp}]")
            out = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=test["prompt"],
                max_gen_len=90,
                temperature=temp,
                device=device
            )
            print(f"RESPUESTA: {out}\n")


if __name__ == "__main__":
    run_benchmark()
