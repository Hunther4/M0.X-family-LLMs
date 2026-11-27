#!/usr/bin/env python3
"""Script de alto rendimiento para descargar, tokenizar y sharder 500M tokens de LatamGPT a formato binario uint16.

Descarga y procesa desde 'latam-gpt/fineweb2-spa_Latn-edu' en streaming directo vía PyArrow C++ engine,
utilizando el Tokenizer BPE oficial de 16k y multiprocessing con ProcessPoolExecutor.
Guarda los tokens directamente en shards binarios compactos (dtype='>u2')
compatibles con BinaryCorpusDataset para un entrenamiento sin carga de RAM ni dependencias de red.
"""

import os
import sys
import time
import json
import argparse
import numpy as np
import concurrent.futures
from pathlib import Path

# Asegurar import de src
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from huggingface_hub import HfFileSystem
import pyarrow.parquet as pq
from src.tokenizer.bpe import Tokenizer

SHARD_SIZE = 25_000_000  # 25 Millones de tokens por shard (50 MB por archivo)
TARGET_TOKENS = 500_000_000  # 500 Millones de tokens objetivo (20 shards)
EOS_TOKEN = 256  # <|endoftext|>

# Worker global
worker_tok = None

def init_worker(tokenizer_path: str):
    global worker_tok
    worker_tok = Tokenizer()
    worker_tok.load(tokenizer_path)

def encode_text_list(texts: list[str]) -> list[int]:
    global worker_tok
    tokens = []
    for text in texts:
        if not text or len(text.strip()) < 20:
            continue
        tokens.extend(worker_tok.encode(text))
        tokens.append(EOS_TOKEN)
    return tokens

def main():
    parser = argparse.ArgumentParser(description="Builder de Corpus Binario LatamGPT 500M")
    parser.add_argument("--output-dir", type=str, default="data/corpus_latam_500m", help="Directorio destino")
    parser.add_argument("--target-tokens", type=int, default=TARGET_TOKENS, help="Tokens objetivo (defecto: 500M)")
    parser.add_argument("--shard-size", type=int, default=SHARD_SIZE, help="Tokens por shard (defecto: 25M)")
    parser.add_argument("--num-workers", type=int, default=4, help="Procesos paralelos (defecto: 4)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer_path = str(REPO_ROOT / "data" / "tokenizers" / "tokenizer.json")

    print("=" * 70)
    print(f"🚀 INICIANDO EXTRACCIÓN Y TOKENIZACIÓN DE {args.target_tokens:,} TOKENS")
    print(f"📁 Directorio de salida: {output_dir}")
    print(f"📦 Tamaño por shard: {args.shard_size:,} tokens ({(args.shard_size * 2) / (1024*1024):.1f} MB)")
    print(f"⚡ Procesos paralelos: {args.num_workers}")
    print("=" * 70)

    # Revisar shards existentes
    existing_shards = sorted(output_dir.glob("shard_*.bin"))
    total_tokens_written = sum(s.stat().st_size // 2 for s in existing_shards)
    shard_idx = len(existing_shards)

    if total_tokens_written >= args.target_tokens:
        print(f"✅ El corpus ya contiene {total_tokens_written:,} tokens en {shard_idx} shards. ¡Listo!")
        return

    if existing_shards:
        print(f"ℹ️ Reanudando desde shard {shard_idx:05d} ({total_tokens_written:,} tokens ya escritos)")

    remote_parquets = [
        "datasets/latam-gpt/fineweb2-spa_Latn-edu/data/train-00000-of-00256.parquet",
        "datasets/latam-gpt/fineweb2-spa_Latn-edu/data/train-00001-of-00256.parquet",
    ]

    fs = HfFileSystem()
    t_start = time.time()
    tokens_buffer = []

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=args.num_workers,
        initializer=init_worker,
        initargs=(tokenizer_path,)
    ) as executor:
        for parquet_path in remote_parquets:
            if total_tokens_written >= args.target_tokens:
                break
            print(f"🌐 Conectando a {parquet_path}...")
            with fs.open(parquet_path, "rb") as f_remote:
                pf = pq.ParquetFile(f_remote)
                # Iterar en lotes de 1,000 documentos
                batch_iter = pf.iter_batches(batch_size=1000, columns=["text"])
                
                # Despachar a los workers en chunks de 250 documentos
                pending_futures = []
                for record_batch in batch_iter:
                    raw_texts = record_batch.column(0).to_pylist()
                    # Dividir en sub-lotes para los workers
                    sub_size = max(1, len(raw_texts) // args.num_workers)
                    for i in range(0, len(raw_texts), sub_size):
                        sub_texts = raw_texts[i:i + sub_size]
                        pending_futures.append(executor.submit(encode_text_list, sub_texts))

                    # Procesar resultados a medida que se completan
                    while len(pending_futures) >= args.num_workers * 2:
                        fut = pending_futures.pop(0)
                        encoded_chunk = fut.result()
                        tokens_buffer.extend(encoded_chunk)

                        # Escribir shard si llegamos al tamaño
                        while len(tokens_buffer) >= args.shard_size and total_tokens_written < args.target_tokens:
                            shard_path = output_dir / f"shard_{shard_idx:05d}.bin"
                            shard_tokens = tokens_buffer[:args.shard_size]
                            tokens_buffer = tokens_buffer[args.shard_size:]

                            arr = np.array(shard_tokens, dtype=">u2")
                            arr.tofile(str(shard_path))

                            total_tokens_written += args.shard_size
                            shard_idx += 1

                            elapsed = time.time() - t_start
                            rate = total_tokens_written / elapsed if elapsed > 0 else 0
                            pct = (total_tokens_written / args.target_tokens) * 100
                            rem_tokens = args.target_tokens - total_tokens_written
                            rem_time = (rem_tokens / rate) / 60 if rate > 0 else 0
                            print(
                                f"💾 Shard {shard_idx:02d} completado ({shard_path.name}) | "
                                f"Tokens: {total_tokens_written:,} / {args.target_tokens:,} ({pct:.1f}%) | "
                                f"Vel: {rate:,.0f} tok/s | Transcurrido: {elapsed/60:.1f}m | Restante: {rem_time:.1f}m"
                            )

                        if total_tokens_written >= args.target_tokens:
                            break
                    if total_tokens_written >= args.target_tokens:
                        break

                # Vaciar futures restantes
                for fut in pending_futures:
                    if total_tokens_written >= args.target_tokens:
                        break
                    encoded_chunk = fut.result()
                    tokens_buffer.extend(encoded_chunk)
                    while len(tokens_buffer) >= args.shard_size and total_tokens_written < args.target_tokens:
                        shard_path = output_dir / f"shard_{shard_idx:05d}.bin"
                        shard_tokens = tokens_buffer[:args.shard_size]
                        tokens_buffer = tokens_buffer[args.shard_size:]
                        arr = np.array(shard_tokens, dtype=">u2")
                        arr.tofile(str(shard_path))
                        total_tokens_written += args.shard_size
                        shard_idx += 1
                        elapsed = time.time() - t_start
                        rate = total_tokens_written / elapsed if elapsed > 0 else 0
                        pct = (total_tokens_written / args.target_tokens) * 100
                        print(
                            f"💾 Shard {shard_idx:02d} completado ({shard_path.name}) | "
                            f"Tokens: {total_tokens_written:,} / {args.target_tokens:,} ({pct:.1f}%) | "
                            f"Vel: {rate:,.0f} tok/s"
                        )

    # Último shard si falta remanente
    if total_tokens_written < args.target_tokens and len(tokens_buffer) >= 1024:
        needed = args.target_tokens - total_tokens_written
        final_tokens = tokens_buffer[:needed]
        shard_path = output_dir / f"shard_{shard_idx:05d}.bin"
        arr = np.array(final_tokens, dtype=">u2")
        arr.tofile(str(shard_path))
        total_tokens_written += len(final_tokens)
        shard_idx += 1
        print(f"💾 Último shard escrito ({shard_path.name}) con {len(final_tokens):,} tokens.")

    # Guardar manifest metadata
    manifest = {
        "dataset_name": "latam-gpt/fineweb2-spa_Latn-edu",
        "total_tokens": total_tokens_written,
        "shards_count": shard_idx,
        "shard_size": args.shard_size,
        "dtype": ">u2",
        "vocab_size": 16384,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    total_time = time.time() - t_start
    print("=" * 70)
    print(f"🎉 ¡EXTRACCIÓN Y TOKENIZACIÓN COMPLETADAS CON ÉXITO!")
    print(f"📊 Total tokens binarios: {total_tokens_written:,}")
    print(f"📦 Total shards: {shard_idx}")
    print(f"⏱️ Tiempo total: {total_time/60:.2f} minutos ({total_tokens_written/total_time:,.0f} tok/s)")
    print(f"💾 Espacio en disco: {(total_tokens_written * 2) / (1024*1024):.2f} MB")
    print(f"📑 Manifest guardado en: {output_dir / 'manifest.json'}")
    print("=" * 70)

if __name__ == "__main__":
    main()
