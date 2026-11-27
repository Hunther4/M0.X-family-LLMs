"""Script para convertir data/corpus wiki-python (*.parquet) a JSONL estructurado para SFT."""

import glob
import json
import os
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = str(REPO_ROOT / "data" / "corpus wiki-python")
OUTPUT_DIR = str(REPO_ROOT / "data" / "corpus_sft")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "wiki_y_codigo_python_87m_tokens_178mb.jsonl")
LEGACY_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "corpus_wiki_python.jsonl")


def convert_wiki_python_to_jsonl():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    parquet_files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.parquet")))
    print(f"[CONVERT] Procesando {len(parquet_files)} archivos parquet en {SOURCE_DIR}...")

    total_samples = 0
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for pfile in parquet_files:
            try:
                df = pd.read_parquet(pfile)
                if 'text' not in df.columns or df.empty:
                    continue
                
                for _, row in df.iterrows():
                    text = str(row['text']).strip()
                    if not text or len(text) < 30:
                        continue
                    
                    # Estructurar la entrada de wiki-python como muestra instructiva
                    entry = {
                        "system": "Eres M0.1, un asistente experto en programación en Python y documentación de software.",
                        "conversation": f"<|user|>\nExplica o documenta la siguiente información técnica sobre Python:\n<|assistant|>\n{text}"
                    }
                    f_out.write(json.dumps(entry, ensure_ascii=False) + '\n')
                    total_samples += 1
            except Exception as e:
                continue

    # Mantener enlace simbólico retrocompatible
    if os.path.islink(LEGACY_OUTPUT_FILE) or not os.path.exists(LEGACY_OUTPUT_FILE):
        if os.path.islink(LEGACY_OUTPUT_FILE):
            os.unlink(LEGACY_OUTPUT_FILE)
        os.symlink(os.path.basename(OUTPUT_FILE), LEGACY_OUTPUT_FILE)

    print(f"[CONVERT] ¡Convertidas {total_samples:,} muestras en {OUTPUT_FILE}!")
    return OUTPUT_FILE


if __name__ == "__main__":
    convert_wiki_python_to_jsonl()
