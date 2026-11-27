#!/usr/bin/env python3
"""Batería de pruebas conversacionales y de conocimiento para M0.1-Mini (69.6M params, 2 expertos)."""

import os
import sys
import torch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.tokenizer.bpe import Tokenizer
from src.inference.generate import generate, GenerationMetrics

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 70)
    print(f"🤖 EVALUACIÓN EN RESPUESTAS: M0.1-MINI (69.6M PARÁMETROS - 2 EXPERTOS)")
    print(f"🔹 Dispositivo: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")
    print("=" * 70)

    # 1. Tokenizer
    tokenizer = Tokenizer()
    tokenizer.load("data/tokenizers/tokenizer.json")

    # 2. Configuración M0.1-Mini (2 expertos, top-1)
    cfg = M01Config(
        vocab_size=16384,
        d_model=640,
        n_heads=10,
        d_ff=1728,
        n_layers=12,
        num_experts=2,
        num_shared_experts=1,
        moe_top_k=1,
        d_ff_shared=448,
        d_ff_routed=784,
    )
    model = TransformerLM(cfg).to(device)

    # 3. Cargar Checkpoint de M0.1 Mini
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="runs/m01_mini_sft/checkpoints/checkpoint.pt")
    args, _ = parser.parse_known_args()
    ckpt_path = args.checkpoint if os.path.exists(args.checkpoint) else "runs/m01_mini/checkpoints/checkpoint.pt"
    print(f"📦 Usando checkpoint: {ckpt_path}")

    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state"], strict=True)
    model.eval()
    vram_mb = torch.cuda.memory_allocated() / (1024 * 1024) if device.type == "cuda" else 0
    print(f"✅ M0.1-Mini cargado en GPU | VRAM: {vram_mb:.1f} MB (Súper ligero)")
    print("=" * 70)

    # Prompts de prueba variados
    prompts = [
        # Conversación e Identidad
        ("<|user|>\nHola, preséntate brevemente.\n<|assistant|>\n", "Identidad y Presentación", 0.4),
        ("<|user|>\n¿Cuál es tu función como modelo de lenguaje?\n<|assistant|>\n", "Función del Modelo", 0.4),

        # Preguntas Fácticas / Mundo
        ("<|user|>\n¿Cuál es la capital de Argentina?\n<|assistant|>\n", "Geografía: Capital de Argentina", 0.3),
        ("<|user|>\nExplica en una oración sencilla qué es el agua.\n<|assistant|>\n", "Ciencia Básica: El Agua", 0.4),

        # Razonamiento Aritmético Elemental
        ("<|user|>\nSi tengo 3 manzanas y me como 1, ¿cuántas manzanas me quedan?\n<|assistant|>\n", "Lógica / Aritmética Simple", 0.2),

        # Código / Programación
        ("<|user|>\nEscribe un código básico en Python para imprimir los números del 1 al 5.\n<|assistant|>\n", "Código: Bucle en Python", 0.2),
        ("def saludar(nombre):\n    \"\"\"Saluda a una persona por su nombre.\"\"\"\n", "Autocompletado de Función", 0.2),

        # Creatividad
        ("<|user|>\nEscribe una frase corta sobre el sol y el amanecer.\n<|assistant|>\n", "Creatividad: Frase poética", 0.5),
    ]

    for idx, (p, cat, temp) in enumerate(prompts, 1):
        print(f"\n--- [Prueba {idx}/8: {cat}] ---")
        prompt_clean = p.strip()
        print(f"📥 Entrada:\n{prompt_clean}")

        metrics = GenerationMetrics()
        with torch.no_grad():
            output = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=p,
                max_gen_len=90,
                temperature=temp,
                top_p=0.9,
                device=device,
                metrics=metrics,
            )

        if "<|assistant|>\n" in output:
            resp = output.split("<|assistant|>\n")[-1].strip()
        else:
            resp = output[len(p):].strip()

        print(f"📤 Respuesta de M0.1-Mini:\n{resp}")
        print(f"⚡ Tiempo: {metrics.total_seconds*1000:.1f}ms ({metrics.tokens_per_second:.1f} tok/s) | Tokens: {metrics.generated_tokens}")
        print("-" * 50)

    print("\n" + "=" * 70)
    print("🏁 EVALUACIÓN DE M0.1-MINI COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    main()
