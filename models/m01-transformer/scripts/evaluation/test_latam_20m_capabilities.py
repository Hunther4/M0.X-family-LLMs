#!/usr/bin/env python3
"""
Batería de pruebas de capacidades para M0.1-Mini tras el entrenamiento de 20M tokens LatamGPT.
Evalúa:
1. Fluidez de texto continuo en español latinoamericano (Pretraining / Completado).
2. Conocimiento general, geografía, ciencia e historia de Latinoamérica / Chile.
3. Razonamiento y lógica estructurada.
4. Generación y completado de código Python.
5. Formato de conversación / instrucción.
"""

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

def main():
    parser = argparse.ArgumentParser(description="Test M0.1-Mini 20M LatamGPT")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="runs/m01_mini_latam_20m/checkpoints/checkpoint_20M.pt",
        help="Ruta al checkpoint a evaluar",
    )
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 75)
    print("🔬 BATERÍA DE PRUEBAS: CAPACIDADES POST-ENTRENAMIENTO 20M LATAMGPT")
    print(f"🔹 Dispositivo: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")
    print(f"📦 Checkpoint: {args.checkpoint}")
    print("=" * 75)

    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.is_absolute():
        ckpt_path = REPO_ROOT / ckpt_path

    # Tokenizer
    tokenizer = Tokenizer()
    tokenizer.load(str(REPO_ROOT / "data/tokenizers/tokenizer.json"))

    # Configuración de arquitectura
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

    test_cases = [
        # CATEGORÍA 1: Completado de texto continuo & conocimiento Latam / Maule / Chile
        {
            "category": "Completado & Conocimiento Regional (Maule / Chile / Latam)",
            "prompt": "La Región del Maule es conocida por su producción agrícola y vitivinícola, destacando ciudades como Talca, Curicó, Linares y Cauquenes, donde",
            "temp": 0.4,
            "max_len": 90,
            "is_chat": False,
        },
        {
            "category": "Completado Educativo / Ciencia General",
            "prompt": "La fotosíntesis es el proceso biológico fundamental mediante el cual las plantas transforman",
            "temp": 0.3,
            "max_len": 90,
            "is_chat": False,
        },
        # CATEGORÍA 2: Razonamiento Matemático y Lógica
        {
            "category": "Lógica y Aritmética",
            "prompt": "Pregunta: Si un tren viaja a 60 kilómetros por hora durante 3 horas y media, ¿cuántos kilómetros recorre en total?\nRespuesta paso a paso:",
            "temp": 0.2,
            "max_len": 90,
            "is_chat": False,
        },
        # CATEGORÍA 3: Código e Ingeniería de Software
        {
            "category": "Programación Python",
            "prompt": "def calcular_promedio(lista_numeros):\n    \"\"\"Calcula el promedio de una lista de flotantes.\"\"\"\n",
            "temp": 0.2,
            "max_len": 80,
            "is_chat": False,
        },
        # CATEGORÍA 4: Formato Instruccional / Diálogo SFT
        {
            "category": "Instrucción Directa (Chat Template)",
            "prompt": "<|user|>\nExplica en dos oraciones claras qué es el aprendizaje automático (Machine Learning).\n<|assistant|>\n",
            "temp": 0.3,
            "max_len": 100,
            "is_chat": True,
        },
        # CATEGORÍA 5: Razonamiento Extendido con <think>
        {
            "category": "Razonamiento con <think>",
            "prompt": "<|user|>\n¿Por qué el cielo se ve azul durante el día?\n<|assistant|>\n<think>\n",
            "temp": 0.3,
            "max_len": 110,
            "is_chat": True,
        }
    ]

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n" + "-" * 75)
        print(f"🧪 Test {idx}/{len(test_cases)}: [{tc['category']}] (Temp: {tc['temp']})")
        print(f"📥 Prompt:\n{tc['prompt']}")
        print("-" * 35 + " Salida " + "-" * 35)

        metrics = GenerationMetrics()
        with torch.no_grad():
            output = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=tc["prompt"],
                max_gen_len=tc["max_len"],
                temperature=tc["temp"],
                top_p=0.9,
                device=device,
                metrics=metrics,
            )

        # Para prompts de chat o directos, mostrar la continuación
        continuation = output[len(tc["prompt"]):]
        print(f"\033[92m{continuation}\033[0m")
        print(f"\n⚡ {metrics.total_seconds*1000:.1f}ms ({metrics.tokens_per_second:.1f} tok/s) | Tokens generados: {metrics.generated_tokens}")

    print("\n" + "=" * 75)
    print("🏁 EVALUACIÓN COMPLETADA CON ÉXITO")
    print("=" * 75)

if __name__ == "__main__":
    main()
