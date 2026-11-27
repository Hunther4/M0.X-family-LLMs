#!/usr/bin/env python3
"""Unificador y validador del corpus de dialecto, identidad y razonamiento extendido M0.1."""

import os
import sys
import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.tokenizer.bpe import Tokenizer

def main():
    print("=" * 70)
    print("🔄 UNIFICACIÓN DEL CORPUS DE DIALECTO Y RAZONAMIENTO EXTENDIDO M0.1")
    print("=" * 70)

    corpus_dir = REPO_ROOT / "data" / "corpus_sft" / "dialect_reasoning"
    output_file = REPO_ROOT / "data" / "corpus_sft" / "corpus_dialecto_razonamiento_unificado.jsonl"
    tokenizer_path = REPO_ROOT / "data" / "tokenizers" / "tokenizer.json"

    tokenizer = Tokenizer()
    tokenizer.load(str(tokenizer_path))

    part_files = sorted(list(corpus_dir.glob("part_*.jsonl")))
    if not part_files:
        print(f"⚠️ Aún no se encontraron archivos part_*.jsonl en {corpus_dir}")
        return

    print(f"📁 Particiones encontradas: {len(part_files)}")
    for f in part_files:
        print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    all_samples = []
    stats_per_part = {}

    for f in part_files:
        lines = []
        tokens_in_part = 0
        think_count = 0
        with open(f, "r", encoding="utf-8") as infile:
            for line_idx, line in enumerate(infile):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    if not text:
                        continue
                    tokens = tokenizer.encode(text)
                    tokens_in_part += len(tokens)
                    if "<think>" in text and "</think>" in text:
                        think_count += 1
                    lines.append(obj)
                except Exception as e:
                    print(f"⚠️ Error en {f.name} línea {line_idx}: {e}")
        stats_per_part[f.name] = {
            "samples": len(lines),
            "tokens": tokens_in_part,
            "think_samples": think_count,
        }
        all_samples.extend(lines)

    print("\n📊 Métricas por Partición:")
    total_tokens = 0
    total_think = 0
    for name, s in stats_per_part.items():
        total_tokens += s["tokens"]
        total_think += s["think_samples"]
        print(f"  • {name:40s}: {s['samples']:5d} muestras | {s['tokens']:8,d} tokens | {s['think_samples']:4d} con <think>")

    print("-" * 70)
    print(f"Total preliminar acumulado: {len(all_samples):,d} muestras | {total_tokens:,d} tokens | {total_think:,d} con <think>")

    if not all_samples:
        return

    # Shuffle determinista para balancear entre temas durante los batches
    random.seed(42)
    random.shuffle(all_samples)

    with open(output_file, "w", encoding="utf-8") as outfile:
        for item in all_samples:
            outfile.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Archivo unificado guardado en: {output_file}")
    print(f"📦 Tamaño en disco: {output_file.stat().st_size / (1024 * 1024):.2f} MB")
    print("=" * 70)

if __name__ == "__main__":
    main()
