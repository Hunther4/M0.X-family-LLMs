#!/usr/bin/env python3
"""Script principal para compilar y validar el Corpus SFT de Identidad, Dialecto y Razonamiento Extendido.

Salida:
data/corpus_sft/dialect_reasoning/part_1_identidad_dialecto.jsonl

Requisitos:
- Entre 50,000 y 100,000 tokens.
- Formato por línea: {"text": "<|user|>\n...\n<|assistant|>\n<think>\n...\n</think>\n..."}
- Validación rigurosa con Tokenizer BPE nativo de M0.1.
"""

import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.tokenizer.bpe import Tokenizer
from scripts.utils.corpus_data import (
    cat1_identidad,
    cat2_arquitectura,
    cat3_dialecto_tono,
    cat4_ingenieria_codigo,
    cat5_matematicas_ml,
    cat6_escenarios_avanzados,
    cat7_dialogos_razonamiento,
    cat8_sistemas_devops,
    cat9_identidad_avanzada
)

OUTPUT_DIR = REPO_ROOT / "data" / "corpus_sft" / "dialect_reasoning"
OUTPUT_FILE = OUTPUT_DIR / "part_1_identidad_dialecto.jsonl"
TOKENIZER_FILE = REPO_ROOT / "data" / "tokenizers" / "tokenizer.json"


def main():
    print("=" * 70)
    print("🚀 COMPILACIÓN DE CORPUS SFT: IDENTIDAD, DIALECTO Y RAZONAMIENTO (<think>)")
    print(f"📁 Directorio de salida: {OUTPUT_DIR}")
    print(f"📄 Archivo destino: {OUTPUT_FILE}")
    print("=" * 70)

    # 1. Asegurar existencia de directorio
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Cargar Tokenizer
    print("🔹 Cargando Tokenizer BPE...")
    tokenizer = Tokenizer()
    tokenizer.load(str(TOKENIZER_FILE))
    print(f"✅ Tokenizer cargado con éxito. Vocabulario: {len(tokenizer.vocab)} tokens.")

    # 3. Recopilar muestras de todos los módulos
    modules = [
        cat1_identidad,
        cat2_arquitectura,
        cat3_dialecto_tono,
        cat4_ingenieria_codigo,
        cat5_matematicas_ml,
        cat6_escenarios_avanzados,
        cat7_dialogos_razonamiento,
        cat8_sistemas_devops,
        cat9_identidad_avanzada
    ]

    all_samples = []
    print("\n📦 Recopilando muestras por categoría:")
    for mod in modules:
        samples = mod.get_samples()
        nombre_cat = mod.__name__.split(".")[-1]
        print(f"  - {nombre_cat:<28}: {len(samples):>3} muestras")
        all_samples.extend(samples)

    total_samples = len(all_samples)
    print(f"\n📊 Total de muestras recopiladas: {total_samples}")

    # 4. Validar formato, unicidad y contar tokens
    print("\n🔍 Validando estructura de muestras y conteo de tokens BPE...")
    total_tokens = 0
    think_tokens_list = []
    seen_prompts = set()
    jsonl_records = []

    for idx, item in enumerate(all_samples, 1):
        user_prompt = item["user"].strip()
        think_content = item["think"].strip()
        response_content = item["response"].strip()

        # Validación de duplicados
        if user_prompt in seen_prompts:
            print(f"⚠️ Advertencia: Prompt duplicado detectado: '{user_prompt[:40]}...'")
        seen_prompts.add(user_prompt)

        # Formatear el texto completo según estándar SFT de M0.1
        formatted_text = f"<|user|>\n{user_prompt}\n<|assistant|>\n<think>\n{think_content}\n</think>\n{response_content}"

        # Codificar y contar tokens
        token_ids = tokenizer.encode(formatted_text)
        token_count = len(token_ids)
        total_tokens += token_count

        # Evaluar tokens del bloque <think>
        think_text = f"<think>\n{think_content}\n</think>"
        think_tokens = len(tokenizer.encode(think_text))
        think_tokens_list.append(think_tokens)

        # Preparar registro JSONL
        jsonl_records.append({"text": formatted_text})

    avg_think = sum(think_tokens_list) / len(think_tokens_list)

    print(f"✅ Validación completada:")
    print(f"   • Muestras únicas: {len(seen_prompts)}")
    print(f"   • Tokens totales generados: {total_tokens:,}")
    print(f"   • Tokens por <think>: Mín={min(think_tokens_list)}, Máx={max(think_tokens_list)}, Promedio={avg_think:.1f}")

    # 5. Comprobar que esté dentro del rango requerido [50,000, 100,000]
    if 50000 <= total_tokens <= 100000:
        print(f"🎉 OBJETIVO CUMPLIDO: {total_tokens:,} tokens se encuentra dentro del rango requerido (50,000 a 100,000 tokens).")
    else:
        print(f"❌ ERROR: El total de tokens ({total_tokens:,}) está fuera del rango [50,000, 100,000].")
        sys.exit(1)

    # 6. Escribir archivo JSONL
    print(f"\n💾 Escribiendo archivo JSONL en: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in jsonl_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"✅ Archivo escrito exitosamente ({OUTPUT_FILE.stat().st_size:,} bytes).")
    print("=" * 70)


if __name__ == "__main__":
    main()
