#!/usr/bin/env python3
"""Batería intensiva de pruebas para M0.1-Mini (69.6M params, 2 expertos) con Dialecto y Razonamiento."""

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

def format_thought_display(text: str) -> str:
    """Separa y da formato legible al pensamiento interno <think> y a la respuesta final."""
    if "<think>" in text:
        parts = text.split("<think>")
        prefix = parts[0].strip()
        rest = parts[1]
        if "</think>" in rest:
            thought, resp = rest.split("</think>", 1)
            thought = thought.strip()
            resp = resp.strip()
            out = ""
            if prefix:
                out += f"{prefix}\n"
            out += "\033[94m┌─ [💭 Razonamiento Retrospectivo / <think>]\033[0m\n"
            for line in thought.split("\n"):
                out += f"\033[94m│\033[0m  {line}\n"
            out += "\033[94m└───────────────────────────────────────────\033[0m\n"
            out += f"\033[1m{resp}\033[0m"
            return out
        else:
            return f"\033[94m[💭 Pensamiento en curso]:\033[0m\n{rest.strip()}"
    return text

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test M0.1-Mini Checkpoints")
    parser.add_argument("--checkpoint", type=str, default="runs/m01_mini_latam_20m/checkpoints/checkpoint_20M.pt", help="Ruta al checkpoint")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 75)
    print("🧪 BATERÍA DE PRUEBAS INTENSIVAS: M0.1-MINI (DIALECTO Y RAZONAMIENTO)")
    print(f"🔹 GPU: {torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'} ({device})")
    
    ckpt_arg = Path(args.checkpoint)
    ckpt_path = ckpt_arg if ckpt_arg.is_absolute() else (REPO_ROOT / ckpt_arg)
    print(f"📦 Checkpoint: {ckpt_path.relative_to(REPO_ROOT) if ckpt_path.is_relative_to(REPO_ROOT) else ckpt_path}")
    print("=" * 75)

    # 1. Cargar Tokenizer
    tokenizer = Tokenizer()
    tokenizer.load(str(REPO_ROOT / "data/tokenizers/tokenizer.json"))

    # 2. Cargar Checkpoint y configurar M0.1-Mini
    ckpt = torch.load(str(ckpt_path), map_location=device, weights_only=False)
    saved_cfg = ckpt.get("model_config", {})
    num_experts = saved_cfg.get("num_experts", 2)
    moe_top_k = saved_cfg.get("moe_top_k", 1)
    d_ff_shared = saved_cfg.get("d_ff_shared", 448)
    d_ff_routed = saved_cfg.get("d_ff_routed", 784)

    cfg = M01Config(
        vocab_size=16384,
        d_model=640,
        n_heads=10,
        d_ff=1728,
        n_layers=12,
        num_experts=num_experts,
        num_shared_experts=1,
        moe_top_k=moe_top_k,
        d_ff_shared=d_ff_shared,
        d_ff_routed=d_ff_routed,
    )
    model = TransformerLM(cfg).to(device)
    model.load_state_dict(ckpt["model_state"], strict=True)
    model.eval()

    vram_mb = torch.cuda.memory_allocated() / (1024 * 1024) if device.type == "cuda" else 0
    print(f"✅ M0.1-Mini listo en VRAM: {vram_mb:.1f} MB | Parámetros: 69.6M\n")

    pruebas = [
        # 1. Identidad básica y dialecto
        {
            "categoria": "1. Identidad y Presentación",
            "prompt": "<|user|>\nHola. ¿Quién eres y qué arquitectura utilizas?\n<|assistant|>\n",
            "max_len": 120,
            "temp": 0.3,
        },
        # 2. Lógica / problema numérico simple
        {
            "categoria": "2. Razonamiento Matemático Simple",
            "prompt": "<|user|>\nSi en una granja hay 4 gallinas y 2 vacas, ¿cuántas patas hay en total?\n<|assistant|>\n",
            "max_len": 130,
            "temp": 0.2,
        },
        # 3. Código Python directo
        {
            "categoria": "3. Código Python - Factorial",
            "prompt": "<|user|>\nEscribe una función en Python para calcular el factorial de un número n.\n<|assistant|>\n",
            "max_len": 140,
            "temp": 0.2,
        },
        # 4. Contexto de Sesión Multiturno (modificación de código previo)
        {
            "categoria": "4. Sesión Multiturno Retrospectiva",
            "prompt": (
                "<|user|>\nDame una lista en Python con los nombres de 3 colores primarios.\n<|assistant|>\n"
                "<think>\nEl usuario pide una lista de 3 colores primarios en Python. Respuesta directa.\n</think>\n"
                "```python\ncolores = ['rojo', 'azul', 'amarillo']\n```\n"
                "<|user|>\nAhora agrega una función que imprima cada color en mayúsculas.\n<|assistant|>\n"
            ),
            "max_len": 140,
            "temp": 0.2,
        },
        # 5. Explicación técnica concisa (cero relleno)
        {
            "categoria": "5. Explicación Técnica Sobria",
            "prompt": "<|user|>\n¿Qué es un Mixture of Experts (MoE) en redes neuronales?\n<|assistant|>\n",
            "max_len": 140,
            "temp": 0.3,
        },
        # 6. Razonamiento de resolución de problemas (troubleshooting)
        {
            "categoria": "6. Troubleshooting / Diagnóstico",
            "prompt": "<|user|>\nMi contenedor Docker falla con exit code 137. ¿Cuál es la causa y cómo lo soluciono?\n<|assistant|>\n",
            "max_len": 150,
            "temp": 0.3,
        },
    ]

    for p in pruebas:
        print("─" * 75)
        print(f"📌 PRUEBA: {p['categoria']}")
        print(f"📥 Entrada:\n{p['prompt'].strip()}")
        print("-" * 40)

        metrics = GenerationMetrics()
        with torch.no_grad():
            output = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=p["prompt"],
                max_gen_len=p["max_len"],
                temperature=p["temp"],
                top_p=0.9,
                device=device,
                metrics=metrics,
            )

        if "<|assistant|>\n" in output:
            resp = output.split("<|assistant|>\n")[-1].strip()
        else:
            resp = output[len(p["prompt"]):].strip()

        print(f"📤 Respuesta del Modelo:\n{format_thought_display(resp)}")
        print(f"\n⏱️ {metrics.total_seconds*1000:.1f}ms ({metrics.tokens_per_second:.1f} tok/s) | Tokens generados: {metrics.generated_tokens}")

    print("\n" + "=" * 75)
    print("🏁 TODAS LAS PRUEBAS COMPLETADAS")
    print("=" * 75)

if __name__ == "__main__":
    main()
