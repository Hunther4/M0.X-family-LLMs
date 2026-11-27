#!/usr/bin/env python3
"""Batería de pruebas de evaluación para Dialecto, Identidad y Razonamiento Extendido (<think>)."""

import os
import sys
import argparse
import torch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.tokenizer.bpe import Tokenizer
from src.inference.generate import generate, GenerationMetrics

def format_colored_thought(text: str) -> str:
    """Formatea las etiquetas <think>...</think> con estilo visual distintivo en terminal."""
    if "<think>" in text and "</think>" in text:
        parts = text.split("<think>")
        prefix = parts[0]
        rest = parts[1].split("</think>")
        thought = rest[0].strip()
        response = rest[1].strip() if len(rest) > 1 else ""

        formatted_thought = f"\033[90m┌─ [Pensamiento Interno / Context Review]\n"
        for line in thought.split("\n"):
            formatted_thought += f"\033[90m│  {line}\n"
        formatted_thought += f"\033[90m└────────────────────────────────────────\033[0m\n"

        return f"{prefix}{formatted_thought}{response}"
    return text

def main():
    parser = argparse.ArgumentParser(description="Test Dialecto & Razonamiento Extendido")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="runs/m01_mini_sft/checkpoints/checkpoint.pt",
        help="Ruta al checkpoint a evaluar",
    )
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 70)
    print("🧠 EVALUACIÓN: DIALECTO, IDENTIDAD Y RAZONAMIENTO RETROSPECTIVO (<think>)")
    print(f"🔹 Dispositivo: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")
    print(f"📦 Checkpoint: {args.checkpoint}")
    print("=" * 70)

    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.is_absolute():
        ckpt_path = REPO_ROOT / ckpt_path

    # 1. Cargar Tokenizer
    tokenizer = Tokenizer()
    tokenizer.load(str(REPO_ROOT / "data/tokenizers/tokenizer.json"))

    # 2. Configurar arquitectura
    ckpt = torch.load(str(ckpt_path), map_location=device, weights_only=False)
    num_experts = 2
    moe_top_k = 1
    if "model_config" in ckpt and hasattr(ckpt["model_config"], "num_experts"):
        num_experts = ckpt["model_config"].num_experts
        moe_top_k = ckpt["model_config"].moe_top_k

    cfg = M01Config(
        vocab_size=16384,
        d_model=640,
        n_heads=10,
        d_ff=1728,
        n_layers=12,
        num_experts=num_experts,
        num_shared_experts=1,
        moe_top_k=moe_top_k,
        d_ff_shared=448,
        d_ff_routed=784,
    )
    model = TransformerLM(cfg).to(device)
    model.load_state_dict(ckpt["model_state"], strict=True)
    model.eval()

    test_prompts = [
        # 1. Identidad y Dialecto Técnico Sobrio
        (
            "<|user|>\n¿Quién eres, cuál es tu arquitectura y cómo fuiste desarrollado?\n<|assistant|>\n",
            "Identidad y Dialecto Técnico",
            0.3,
            120,
        ),
        # 2. Razonamiento Retrospectivo Multiturno
        (
            "<|user|>\nNecesito una función en Python para invertir una cadena de texto.\n<|assistant|>\n"
            "<think>\nEl usuario solicita invertir una cadena. En Python la forma más idiomática y eficiente es mediante slicing [::-1].\n</think>\n"
            "Puedes usar slicing directo:\n```python\ndef invertir_cadena(texto: str) -> str:\n    return texto[::-1]\n```\n"
            "<|user|>\nAhora modifícala para que además elimine los espacios en blanco antes de invertirla.\n<|assistant|>\n",
            "Razonamiento de Sesión Multiturno",
            0.3,
            130,
        ),
        # 3. Razonamiento Matemático / Aritmético con <think>
        (
            "<|user|>\nUn tanque tiene 120 litros. Se vacía a razón de 15 litros por minuto mientras ingresan 5 litros por minuto. ¿En cuántos minutos se vacía por completo?\n<|assistant|>\n",
            "Matemáticas y Lógica con <think>",
            0.2,
            120,
        ),
        # 4. Código con casos de borde
        (
            "<|user|>\nEscribe una función en Python que encuentre el segundo número más grande en una lista desordenada sin ordenar la lista completa.\n<|assistant|>\n",
            "Algoritmos y Casos de Borde con <think>",
            0.2,
            140,
        ),
        # 5. Asistencia Directa sin Fluff
        (
            "<|user|>\n¿Cuál es la diferencia técnica entre una base de datos relacional (SQL) y una no relacional (NoSQL)?\n<|assistant|>\n",
            "Asistente Directo sin Relleno",
            0.3,
            140,
        ),
    ]

    for idx, (p, cat, temp, max_len) in enumerate(test_prompts, 1):
        print(f"\n--- [Test {idx}/{len(test_prompts)}: {cat}] ---")
        prompt_display = p.strip()
        print(f"📥 Entrada:\n{prompt_display}")

        metrics = GenerationMetrics()
        with torch.no_grad():
            output = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=p,
                max_gen_len=max_len,
                temperature=temp,
                top_p=0.9,
                device=device,
                metrics=metrics,
            )

        if "<|assistant|>\n" in output:
            resp = output.split("<|assistant|>\n")[-1].strip()
        else:
            resp = output[len(p):].strip()

        print(f"\n📤 Salida:")
        print(format_colored_thought(resp))
        print(f"⚡ {metrics.total_seconds*1000:.1f}ms ({metrics.tokens_per_second:.1f} tok/s) | Tokens: {metrics.generated_tokens}")
        print("-" * 60)

    print("\n" + "=" * 70)
    print("🏁 EVALUACIÓN DE DIALECTO Y RAZONAMIENTO COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
