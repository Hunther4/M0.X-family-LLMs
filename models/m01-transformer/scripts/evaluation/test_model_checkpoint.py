#!/usr/bin/env python3
"""Script de pruebas de inferencia para M0.1 Transformer en el checkpoint actual."""

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
from src.inference.generate import generate

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🔹 Dispositivo: {device}")
    if device.type == "cuda":
        print(f"🔹 GPU: {torch.cuda.get_device_name(0)}")

    # 1. Cargar Tokenizer
    tok_path = "data/tokenizers/tokenizer.json"
    tokenizer = Tokenizer()
    tokenizer.load(tok_path)
    print(f"🔹 Tokenizer cargado desde {tok_path} (vocab: {len(tokenizer.vocab)})")

    # 2. Inicializar Modelo
    cfg = M01Config(vocab_size=16384)
    model = TransformerLM(cfg).to(device)

    # 3. Cargar Checkpoint Canónico
    ckpt_path = "runs/run_multi_checkpoint_100steps/checkpoints/checkpoint.pt"
    if not os.path.exists(ckpt_path):
        print(f"❌ Error: Checkpoint no encontrado en {ckpt_path}")
        return

    print(f"🔹 Cargando pesos desde: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    step = ckpt.get("step", "N/A")
    state_dict = ckpt.get("model_state", ckpt)
    
    # Manejar posibles prefijos
    cleaned_state = {}
    for k, v in state_dict.items():
        clean_k = k.replace("_orig_mod.", "").replace("model.", "")
        cleaned_state[clean_k] = v
        
    model.load_state_dict(cleaned_state, strict=False)
    model.eval()
    print(f"✅ Modelo M0.1 listo en Modo Evaluación (Checkpoint Paso: {step})")
    print("=" * 70)

    # Batería de Pruebas
    prompts = [
        # 1. Identidad y cortesía
        ("<|user|>\n¿Quién eres y cuál es tu función?\n<|assistant|>\n", "Identidad del Modelo"),
        ("<|user|>\nHola, ¿cómo estás hoy?\n<|assistant|>\n", "Conversación y Saludo"),
        
        # 2. Geografía y Conocimiento de Mundo
        ("<|user|>\n¿Cuál es la capital de Chile?\n<|assistant|>\n", "Geografía: Capital de Chile"),
        ("<|user|>\n¿En qué continente queda Francia y cuál es su capital?\n<|assistant|>\n", "Geografía: Europa / Francia"),
        
        # 3. Ciencia y Conceptos
        ("<|user|>\nExplica brevemente qué es la fotosíntesis.\n<|assistant|>\n", "Ciencia: Fotosíntesis"),
        ("<|user|>\n¿Por qué el cielo se ve azul durante el día?\n<|assistant|>\n", "Física: Color del cielo"),

        # 4. Programación básica
        ("<|user|>\nEscribe una función en Python para sumar dos números.\n<|assistant|>\n", "Programación: Función suma Python"),
        
        # 5. Creatividad y Literatura
        ("<|user|>\nEscribe un verso corto sobre la noche y las estrellas.\n<|assistant|>\n", "Creatividad: Poesía nocturna"),
    ]

    for idx, (p, cat) in enumerate(prompts, 1):
        print(f"\n--- [Prueba {idx}/8: {cat}] ---")
        prompt_display = p.strip()
        print(f"📥 Prompt:\n{prompt_display}")
        
        # Generar con temperatura 0.5 para coherencia
        with torch.no_grad():
            output = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=p,
                max_gen_len=120,
                temperature=0.5,
                top_p=0.9,
                device=device,
            )
        
        # Extraer respuesta del asistente
        if "<|assistant|>\n" in output:
            resp = output.split("<|assistant|>\n")[-1].strip()
        else:
            resp = output[len(p):].strip()
            
        print(f"📤 Respuesta del Modelo:\n{resp}")
        print("-" * 50)

    print("\n" + "=" * 70)
    print("🏁 Batería de Pruebas Finalizada.")
    print("=" * 70)

if __name__ == "__main__":
    main()
