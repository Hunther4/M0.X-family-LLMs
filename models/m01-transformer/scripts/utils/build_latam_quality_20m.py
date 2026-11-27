#!/usr/bin/env python3
"""Filtro y constructor del corpus educativo y cultural de alta calidad de 20M tokens de LatamGPT.

Extrae textos de alta calidad de 'latam-gpt/fineweb2-spa_Latn-edu' vía streaming remoto PyArrow,
aplicando filtros rigurosos de idioma (FastText >= 0.95), puntaje educativo (score >= 3.0),
limpieza de spam/anuncios y conteo exacto de tokens mediante el Tokenizer BPE oficial de 16k.

Salida: data/corpus_sft/latam_quality_20m.jsonl
"""

import os
import sys
import re
import time
import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from huggingface_hub import HfFileSystem
import pyarrow.parquet as pq
from src.tokenizer.bpe import Tokenizer

TARGET_TOKENS = 20_000_000
MIN_LANG_SCORE = 0.95
MIN_EDU_SCORE = 3.0
MIN_CHAR_LEN = 150
MAX_CHAR_LEN = 50_000  # Evita volcados gigantescos únicos

# Palabras prohibidas / spam / SEO junk
BLACK_LIST_TERMS = [
    "casino online", "tragamonedas", "apuestas deportivas", "ruleta en vivo",
    "viagra", "cialis", "xxx", "porn", "sexo gratis", "escort", "prepago",
    "todos los derechos reservados. politica de privacidad",
    "usamos cookies para asegurar que damos la mejor experiencia",
    "haga clic aquí para aceptar las cookies",
]

def is_clean_text(text: str) -> bool:
    if not text or len(text) < MIN_CHAR_LEN:
        return False
    
    text_lower = text.lower()
    for bad in BLACK_LIST_TERMS:
        if bad in text_lower:
            return False
            
    # Verificar ratio de caracteres alfanuméricos
    alnum_count = sum(1 for c in text if c.isalnum())
    if alnum_count / len(text) < 0.65:
        return False
        
    return True

def sanitize_text(text: str) -> str:
    # Reducir repeticiones excesivas de saltos de línea y espacios
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Builder de Corpus de Calidad LatamGPT 20M")
    parser.add_argument("--target-tokens", type=int, default=TARGET_TOKENS, help="Tokens objetivo (defecto: 20M)")
    parser.add_argument("--output", type=str, default="data/corpus_sft/latam_quality_20m.jsonl", help="Ruta de salida JSONL")
    parser.add_argument("--edu-score-min", type=float, default=MIN_EDU_SCORE, help="Score educativo mínimo (defecto: 3.0)")
    parser.add_argument("--lang-score-min", type=float, default=MIN_LANG_SCORE, help="Score idioma mínimo (defecto: 0.95)")
    parser.add_argument("--batch-row-groups", type=int, default=10, help="Row groups por lote de lectura (defecto: 10)")
    args = parser.parse_args()

    out_path = REPO_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print(f"🌟 CONSTRUCTOR DE CORPUS DE CALIDAD LATAMGPT ({args.target_tokens:,} TOKENS)")
    print(f"🎯 Filtro Calidad Educativa: score >= {args.edu_score_min}")
    print(f"🌐 Filtro Pureza Idioma: language_score >= {args.lang_score_min}")
    print(f"📁 Archivo destino: {out_path}")
    print("=" * 75)

    print("⚙️ Cargando Tokenizer oficial M0.1...")
    tokenizer = Tokenizer()
    tokenizer.load(str(REPO_ROOT / "data" / "tokenizers" / "tokenizer.json"))

    fs = HfFileSystem()
    parquet_shards = [
        "datasets/latam-gpt/fineweb2-spa_Latn-edu/data/train-00000-of-00256.parquet",
        "datasets/latam-gpt/fineweb2-spa_Latn-edu/data/train-00001-of-00256.parquet",
    ]

    total_tokens = 0
    total_docs = 0
    t_start = time.time()
    
    score_sum = 0.0
    scores_above_4 = 0

    with open(out_path, "w", encoding="utf-8") as f_out:
        for shard_idx, parquet_path in enumerate(parquet_shards):
            if total_tokens >= args.target_tokens:
                break

            print(f"\n📡 Conectando a shard remoto: {parquet_path}...")
            with fs.open(parquet_path, "rb") as f_remote:
                pf = pq.ParquetFile(f_remote)
                num_row_groups = pf.num_row_groups
                print(f"📄 Shard abierto. Total row groups disponibles: {num_row_groups}")

                rg_step = args.batch_row_groups
                for start_rg in range(0, num_row_groups, rg_step):
                    if total_tokens >= args.target_tokens:
                        break

                    end_rg = min(start_rg + rg_step, num_row_groups)
                    rgs_to_read = list(range(start_rg, end_rg))

                    t_read_start = time.time()
                    try:
                        table = pf.read_row_groups(rgs_to_read, columns=["text", "score", "language_score"])
                    except Exception as e:
                        print(f"⚠️ Error leyendo row groups {start_rg}..{end_rg}: {e}. Reintentando...")
                        time.sleep(2)
                        table = pf.read_row_groups(rgs_to_read, columns=["text", "score", "language_score"])

                    texts = table["text"].to_pylist()
                    scores = table["score"].to_pylist()
                    langs = table["language_score"].to_pylist()

                    # Procesar y tokenizar documentos
                    batch_tokens = 0
                    batch_docs = 0

                    for text, score, lang in zip(texts, scores, langs):
                        if total_tokens >= args.target_tokens:
                            break

                        if score is None or lang is None:
                            continue
                        if score < args.edu_score_min or lang < args.lang_score_min:
                            continue

                        clean_t = sanitize_text(text)
                        if not is_clean_text(clean_t):
                            continue

                        # Si el texto excede MAX_CHAR_LEN, truncar inteligentemente
                        if len(clean_t) > MAX_CHAR_LEN:
                            clean_t = clean_t[:MAX_CHAR_LEN].rsplit("\n", 1)[0]

                        # Tokenizar para conteo exacto
                        doc_tokens = tokenizer.encode(clean_t)
                        n_tok = len(doc_tokens)
                        if n_tok < 40:
                            continue

                        # Si este documento supera ligeramente el objetivo, guardarlo completo para no romper la semántica
                        f_out.write(json.dumps({"text": clean_t}, ensure_ascii=False) + "\n")
                        
                        total_tokens += n_tok
                        total_docs += 1
                        batch_tokens += n_tok
                        batch_docs += 1
                        score_sum += score
                        if score >= 4.0:
                            scores_above_4 += 1

                    elapsed = time.time() - t_start
                    pct = (total_tokens / args.target_tokens) * 100
                    rate = total_tokens / elapsed if elapsed > 0 else 0
                    rem_tokens = max(0, args.target_tokens - total_tokens)
                    eta_sec = rem_tokens / rate if rate > 0 else 0

                    print(
                        f"  [RG {start_rg:>4}..{end_rg:<4}] "
                        f"Docs: {total_docs:,} (+{batch_docs}) | "
                        f"Tokens: {total_tokens:,} / {args.target_tokens:,} ({pct:5.1f}%) | "
                        f"Vel: {rate:,.0f} tok/s | ETA: {eta_sec/60:4.1f} min"
                    )

    elapsed_total = time.time() - t_start
    size_mb = out_path.stat().st_size / (1024 * 1024)
    avg_score = (score_sum / total_docs) if total_docs > 0 else 0.0

    print("\n" + "=" * 75)
    print("✅ CORPUS LATAMGPT 20M FILTRADO Y GENERADO CON ÉXITO")
    print(f"📁 Archivo: {out_path}")
    print(f"📊 Total tokens reales: {total_tokens:,}")
    print(f"📝 Total documentos: {total_docs:,} (Promedio: {total_tokens/total_docs:.1f} tok/doc)")
    print(f"⭐ Score educativo promedio: {avg_score:.2f} / 5.0 (>= 4.0: {scores_above_4:,} docs)")
    print(f"💾 Tamaño de archivo: {size_mb:.2f} MB")
    print(f"⏱️ Tiempo total: {elapsed_total/60:.2f} minutos ({total_tokens/elapsed_total:,.0f} tok/s)")
    print("=" * 75)

if __name__ == "__main__":
    main()
