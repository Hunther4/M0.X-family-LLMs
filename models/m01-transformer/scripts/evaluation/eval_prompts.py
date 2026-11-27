"""Script para evaluar M0.1 con 20 prompts heterogéneos post-SFT."""

import os
import sys
import torch

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.tokenizer.bpe import Tokenizer
from src.inference.generate import generate
from src.engine_v2.checkpoint_v2 import safe_load_checkpoint, normalize_checkpoint_state

PROMPTS_EVAL = [
    # 1. Identidad y Filosofía
    "¿Quién eres y cuál es tu propósito?",
    "Explica tu arquitectura Mixture of Experts (MoE).",
    "¿Puedes cometer errores al responder?",
    "¿Cuál es tu filosofía de trabajo con los desarrolladores?",
    
    # 2. Desarrollo y Código
    "Los principios SOLID son",
    "Explica qué es np.memmap en Python y para qué sirve.",
    "¿Cómo se define una función en Python?",
    "¿Qué es la Arquitectura Limpia en software?",

    # 3. Razonamiento y Matemáticas
    "Si tengo 3 cajas con 12 manzanas cada una y regalo 10, ¿cuántas manzanas me quedan?",
    "¿Cuál es el 15% de 840?",
    "Un tren viaja a 90 km/h y debe recorrer 270 km, ¿cuánto tarda?",
    "Si el 60% de 200 alumnos aprobó, ¿cuántos reprobaron?",

    # 4. Conocimiento General
    "¿Qué significa DNA?",
    "¿Cuál es la fórmula para calcular el área de un rectángulo?",
    "¿Cuántos días hay en un año estándar?",
    "¿Cuántas horas hay en 5 días y medio?",

    # 5. Estructura de Instrucción y Conversación
    "<|user|>\nHola M0.1, ¿puedes ayudarme a programar?\n<|assistant|>\n",
    "<|user|>\n¿Cuáles son las ventajas de la atención MLA?\n<|assistant|>\n",
    "<|user|>\nDame un consejo de buenas prácticas en Python.\n<|assistant|>\n",
    "<|user|>\n¿Cuál es la velocidad de la luz?\n<|assistant|>\n"
]


def run_eval():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    checkpoint_path = "runs/run_sft_1m_b8/checkpoints/checkpoint.pt"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[EVAL] Dispositivo: {device}")
    print(f"[EVAL] Cargando checkpoint SFT: {checkpoint_path}")

    state = safe_load_checkpoint(checkpoint_path, map_location=device)
    state = normalize_checkpoint_state(state, require_architecture=True)
    config_dict = state["model_config"]
    valid_fields = set(M01Config.__dataclass_fields__)
    config = M01Config(**{k: v for k, v in config_dict.items() if k in valid_fields})

    model = TransformerLM(config).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()

    tokenizer_path = os.path.join("data", "tokenizers", "tokenizer.json")
    tokenizer = Tokenizer()
    if os.path.exists(tokenizer_path):
        print(f"[EVAL] Cargando Tokenizer de 16k desde {tokenizer_path}...")
        tokenizer.load(tokenizer_path)
    else:
        print("[WARNING] Tokenizer de 16k no encontrado!")

    print("\n" + "=" * 70)
    print("         M0.1 — EVALUACIÓN INTERACTIVA POST-SFT (20 PROMPTS)")
    print("=" * 70 + "\n")

    for i, p in enumerate(PROMPTS_EVAL, 1):
        print(f"--- Prompt #{i} ---")
        print(f"ENTRADA: {p}")
        out = generate(
            model=model,
            tokenizer=tokenizer,
            prompt=p,
            max_gen_len=70,
            temperature=0.3,
            device=device
        )
        print(f"SALIDA: {out}\n")


if __name__ == "__main__":
    run_eval()
