#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script de generación y validación del corpus SFT: dialecto y asistencia directa sin fluff.

Genera part_4_asistente_dialecto.jsonl con conteo y validación estricta de tokens.
"""

import os
import sys
import json
import re
from pathlib import Path

# Añadir ruta base del repositorio para importar el tokenizer
BASE_DIR = Path("/mnt/d/Estuding/models/m01-transformer")
sys.path.insert(0, str(BASE_DIR))

from src.tokenizer.bpe import Tokenizer
from scripts.utils.part4_data_science import SCIENCE_SAMPLES
from scripts.utils.part4_data_humanities import HUMANITIES_SAMPLES
from scripts.utils.part4_data_analysis import ANALYSIS_SAMPLES
from scripts.utils.part4_data_formal import FORMAL_SAMPLES
from scripts.utils.part4_data_reasoning import REASONING_SAMPLES

OUTPUT_PATH = BASE_DIR / "data/corpus_sft/dialect_reasoning/part_4_asistente_dialecto.jsonl"
TOKENIZER_PATH = BASE_DIR / "data/tokenizers/tokenizer.json"

FLUFF_PATTERNS = [
    r"¡?Hola!?",
    r"Qué excelente pregunta",
    r"Buena pregunta",
    r"Con gusto te ayudo",
    r"Espero haberte ayudado",
    r"No dudes en consultar",
    r"Como modelo de lenguaje",
    r"Claro que sí",
]

def main():
    print("Iniciando generación de corpus SFT parte 4 (Dialecto y Asistencia Directa)...")
    
    # 1. Cargar Tokenizer
    tok = Tokenizer()
    tok.load(str(TOKENIZER_PATH))
    print(f"Tokenizer cargado desde: {TOKENIZER_PATH}")
    
    # 2. Recopilar y clasificar muestras
    categories = [
        ("Ciencia y Tecnología", SCIENCE_SAMPLES),
        ("Humanidades, Derecho y Economía", HUMANITIES_SAMPLES),
        ("Análisis de Textos y Retórica", ANALYSIS_SAMPLES),
        ("Redacción Formal e Institucional", FORMAL_SAMPLES),
        ("Razonamiento Reflexivo (<think>)", REASONING_SAMPLES),
    ]
    
    all_records = []
    category_stats = {}
    
    # Validar ausencia de fluff y formato estricto
    for cat_name, samples in categories:
        cat_tokens = 0
        for s in samples:
            user_text = s["user"].strip()
            assistant_text = s["assistant"].strip()
            
            # Formato estándar de conversación
            text = f"<|user|>\n{user_text}\n<|assistant|>\n{assistant_text}"
            
            # Verificación de fluff
            for pat in FLUFF_PATTERNS:
                # Si aparece en el assistant fuera de una cita o ejemplo textual
                m = re.search(pat, assistant_text, re.IGNORECASE)
                if m:
                    # Permitir si está dentro de un ejemplo analítico
                    span = m.span()
                    prefix = assistant_text[max(0, span[0]-25):span[0]]
                    if "«" not in prefix and '"' not in prefix and "ej." not in prefix and "Ejemplo" not in prefix:
                        print(f"ALERTA: Posible fluff detectado: '{m.group(0)}' en respuesta: {assistant_text[:60]}...")
            
            # Verificación del bloque <think> si existe
            think_match = re.search(r"<think>(.*?)</think>", assistant_text, re.DOTALL)
            if think_match:
                th_tokens = len(tok.encode(think_match.group(1).strip()))
                if th_tokens < 30 or th_tokens > 85:
                    print(f"AVISO: Bloque <think> con {th_tokens} tokens (fuera del rango ideal 30-80).")
            
            tokens = tok.encode(text)
            n_tokens = len(tokens)
            cat_tokens += n_tokens
            
            all_records.append({
                "json_data": {"text": text},
                "tokens": n_tokens,
                "category": cat_name
            })
            
        category_stats[cat_name] = {
            "samples": len(samples),
            "tokens": cat_tokens,
            "avg_tokens": cat_tokens / len(samples) if samples else 0
        }

    # 3. Intercalar de forma balanceada las categorías para homogeneidad del dataset
    # Mezclamos de forma determinista para que no queden todos los de una categoría juntos
    import random
    rng = random.Random(42)
    rng.shuffle(all_records)
    
    # 4. Escribir archivo de salida
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    total_tokens = 0
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r["json_data"], ensure_ascii=False) + "\n")
            total_tokens += r["tokens"]
            
    # 5. Verificación de relectura y conteo final
    verified_lines = 0
    verified_tokens = 0
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            txt = obj["text"]
            verified_lines += 1
            verified_tokens += len(tok.encode(txt))
            
    assert verified_lines == len(all_records), "Discrepancia en número de líneas"
    assert verified_tokens == total_tokens, "Discrepancia en conteo de tokens"
    
    print("\n" + "="*60)
    print("RESUMEN DE GENERACIÓN CORPUS SFT - PARTE 4")
    print("="*60)
    for cat_name, stats in category_stats.items():
        print(f"- {cat_name:35s}: {stats['samples']:3d} muestras | {stats['tokens']:6d} tokens (promedio: {stats['avg_tokens']:.1f})")
    print("-"*60)
    print(f"TOTAL MUESTRAS GENERADAS : {verified_lines}")
    print(f"TOTAL TOKENS GENERADOS   : {verified_tokens}")
    print(f"UBICACIÓN DEL ARCHIVO    : {OUTPUT_PATH}")
    print(f"TAMAÑO EN DISCO          : {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB")
    print("="*60)
    
    # Validar umbral
    if 50000 <= verified_tokens <= 100000:
        print(f"ÉXITO: Conteo de tokens ({verified_tokens}) dentro del rango objetivo [50,000 - 100,000].")
    else:
        print(f"ADVERTENCIA: Conteo de tokens ({verified_tokens}) fuera del rango objetivo.")

if __name__ == "__main__":
    main()
