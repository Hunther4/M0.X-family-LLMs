#!/usr/bin/env python3
"""Pruebas de código, autocompletado y escalado de contexto máximo para M0.1 Transformer."""

import os
import sys
import time
import torch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.tokenizer.bpe import Tokenizer
from src.inference.generate import generate, GenerationMetrics

def format_mem():
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / (1024 * 1024)
        res = torch.cuda.memory_reserved() / (1024 * 1024)
        return f"Alloc: {alloc:.1f} MB | Res: {res:.1f} MB"
    return "CPU"

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 75)
    print(f"🔬 EVALUACIÓN DE CÓDIGO, AUTOCOMPLETADO Y CONTEXTO LARGO (M0.1 TRANSFORMER)")
    print(f"🔹 Dispositivo: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")
    print("=" * 75)

    # 1. Cargar Tokenizer
    tok_path = "data/tokenizers/tokenizer.json"
    tokenizer = Tokenizer()
    tokenizer.load(tok_path)

    # 2. Cargar Modelo y Checkpoint
    cfg = M01Config(vocab_size=16384)
    model = TransformerLM(cfg).to(device)

    ckpt_path = "runs/run_multi_checkpoint_100steps/checkpoints/checkpoint.pt"
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    step = ckpt.get("step", "N/A")
    state_dict = ckpt.get("model_state", ckpt)
    cleaned_state = {k.replace("_orig_mod.", "").replace("model.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(cleaned_state, strict=False)
    model.eval()
    print(f"✅ Checkpoint cargado exitosamente (Paso: {step}) | VRAM Base: {format_mem()}")
    print("=" * 75)

    # =========================================================================
    # PARTE 1: PRUEBAS DE CÓDIGO Y AUTOCOMPLETADO
    # =========================================================================
    print("\n" + "#" * 30 + " PARTE 1: CÓDIGO Y AUTOCOMPLETADO " + "#" * 30)

    code_tests = [
        (
            "Autocompletado de Función Recursiva (Fibonacci)",
            'def fibonacci(n):\n    """Calcula el n-ésimo número de Fibonacci."""\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    else:\n',
            80,
            0.2,  # temperatura baja para código determinista
        ),
        (
            "Autocompletado de Clase y Método Python",
            "class GestorArchivos:\n    def __init__(self, ruta: str):\n        self.ruta = ruta\n        self.archivos = []\n\n    def leer_contenido(self):\n",
            90,
            0.2,
        ),
        (
            "Instrucción SFT: Función para filtrar pares",
            "<|user|>\nEscribe una función en Python llamada 'filtrar_pares' que reciba una lista de números y devuelva solo los números pares.\n<|assistant|>\n",
            100,
            0.4,
        ),
        (
            "Autocompletado de Consulta SQL / Datos",
            "SELECT usuario_id, COUNT(*) as total_compras, SUM(monto) as gasto_total\nFROM transacciones\nWHERE fecha >= '2026-01-01'\nGROUP BY",
            60,
            0.2,
        ),
    ]

    for title, prompt, max_len, temp in code_tests:
        print(f"\n>>> [TEST CÓDIGO]: {title}")
        print(f"📥 Prompt / Prefijo:\n```\n{prompt}\n```")
        
        metrics = GenerationMetrics()
        with torch.no_grad():
            output = generate(
                model=model,
                tokenizer=tokenizer,
                prompt=prompt,
                max_gen_len=max_len,
                temperature=temp,
                top_p=0.9,
                device=device,
                metrics=metrics,
            )
        
        # Mostrar lo que autocompletó (el texto nuevo después del prompt)
        continuation = output[len(prompt):]
        print(f"📤 Autocompletado del Modelo:\n```\n{continuation}\n```")
        print(f"⏱️ Prefill: {metrics.prefill_seconds*1000:.1f}ms | Decode: {metrics.tokens_per_second:.1f} tok/s | Tokens gen: {metrics.generated_tokens}")
        print("-" * 70)

    # =========================================================================
    # PARTE 2: LLENADO DE CONTEXTO MÁXIMO (ESCALADO DE PREFILL Y GENERACIÓN)
    # =========================================================================
    print("\n" + "#" * 28 + " PARTE 2: ESCALADO DE CONTEXTO MÁXIMO " + "#" * 28)

    # Base de código repetitiva estructurada para inflar contexto sintácticamente válido
    code_block_unit = (
        "def procesar_lote_datos(registro_id: int, metadatos: dict) -> bool:\n"
        "    validado = False\n"
        "    if 'timestamp' in metadatos and metadatos['score'] > 0.5:\n"
        "        validado = True\n"
        "    return validado\n\n"
    )
    unit_ids = tokenizer.encode(code_block_unit)
    unit_tokens = len(unit_ids)
    print(f"🔹 Bloque unitario de código: {unit_tokens} tokens")

    # Niveles de contexto a probar: 1,024 -> 4,096 -> 8,192 -> 16,384 tokens
    target_contexts = [1024, 4096, 8192, 16384]

    for target_ctx in target_contexts:
        repeats = max(1, target_ctx // unit_tokens)
        long_prompt = code_block_unit * repeats
        
        # Añadir al final un disparador de autocompletado
        long_prompt += "# Función principal de ejecución:\ndef main():\n"
        
        prompt_tokens = len(tokenizer.encode(long_prompt))
        print(f"\n>>> [TEST CONTEXTO]: Objetivo ~{target_ctx:,} tokens | Prompt real: {prompt_tokens:,} tokens")
        
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()
        
        metrics = GenerationMetrics()
        try:
            with torch.no_grad():
                output = generate(
                    model=model,
                    tokenizer=tokenizer,
                    prompt=long_prompt,
                    max_gen_len=40,
                    temperature=0.3,
                    top_p=0.9,
                    device=device,
                    metrics=metrics,
                )
            
            elapsed = time.perf_counter() - t0
            continuation = output[len(long_prompt):]
            peak_vram = torch.cuda.max_memory_reserved() / (1024 * 1024)
            alloc_vram = torch.cuda.memory_allocated() / (1024 * 1024)
            
            print(f"✅ ÉXITO: Contexto de {prompt_tokens:,} tokens procesado.")
            print(f"📊 Métricas: Prefill: {metrics.prefill_seconds*1000:.1f}ms | Decode: {metrics.tokens_per_second:.1f} tok/s | VRAM Peak: {peak_vram:.1f} MB | VRAM Alloc: {alloc_vram:.1f} MB")
            print(f"📤 Respuesta generada al final del contexto:\n```\n{continuation}\n```")
        except Exception as e:
            print(f"❌ Error al procesar contexto {target_ctx}: {e}")
        
        print("-" * 70)

    print("\n" + "=" * 75)
    print("🏁 EVALUACIÓN FINALIZADA CON ÉXITO")
    print("=" * 75)

if __name__ == "__main__":
    main()
