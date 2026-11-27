#!/usr/bin/env python3
"""Generador de corpus en español filtrado y equilibrado de 2M tokens para recalibrar M0.1-Mini."""

import os
import sys
import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.tokenizer.bpe import Tokenizer

TARGET_TOKENS = 2_000_000

def main():
    print("=" * 70)
    print("📦 GENERANDO CORPUS EN ESPAÑOL FILTRADO (2M TOKENS)")
    print("=" * 70)

    tokenizer = Tokenizer()
    tokenizer.load("data/tokenizers/tokenizer.json")

    sources = [
        ("data/ya_usados/instrucciones_sft_conversaciones_1m_tokens.jsonl", 1_000_000),
        ("data/ya_usados/distilacion_espanol_unificada_ll028987.jsonl", 1_000_000),
    ]

    samples = []
    total_tokens = 0

    for path, max_tokens in sources:
        if not os.path.exists(path):
            print(f"⚠️ Archivo no encontrado: {path}")
            continue

        print(f"📖 Leyendo desde {path} (objetivo: {max_tokens:,} tokens)...")
        source_tokens = 0
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            random.seed(42)
            random.shuffle(lines)

            for line in lines:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                    # Extraer texto representativo
                    text = ""
                    if "conversation" in d:
                        text = d["conversation"]
                    elif "text" in d or "texto" in d:
                        text = d.get("text") or d.get("texto")
                    elif "prompt" in d and "response" in d:
                        text = f"<|user|>\n{d['prompt']}\n<|assistant|>\n{d['response']}"

                    if not text or "<tool_call>" in text:
                        continue

                    n_tok = len(tokenizer.encode(text))
                    samples.append(json.dumps(d, ensure_ascii=False))
                    source_tokens += n_tok
                    total_tokens += n_tok

                    if source_tokens >= max_tokens:
                        break
                except Exception:
                    continue

        print(f"   -> Recopilados {source_tokens:,} tokens.")

    # Mezclar muestras
    random.seed(42)
    random.shuffle(samples)

    out_path = "data/corpus_sft/corpus_espanol_filtrado_2m.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f_out:
        for s in samples:
            f_out.write(s + "\n")

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print("=" * 70)
    print(f"✅ Corpus generado exitosamente: {out_path}")
    print(f"📊 Total de tokens: {total_tokens:,}")
    print(f"📝 Total de muestras: {len(samples):,}")
    print(f"💾 Tamaño en disco: {size_mb:.2f} MB")
    print("=" * 70)

if __name__ == "__main__":
    main()
