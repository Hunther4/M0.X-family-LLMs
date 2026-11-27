"""Script para descargar y construir un Corpus SFT de Alta Calidad (1M+ Tokens) en Español.

Fuentes:
1. `somosnlp/somos-clean-alpaca-es` (Diálogos limpios y validados de instrucción en español)
2. `FreedomIntelligence/evol-instruct-spanish` (Razonamiento lógico y programación en español)
3. Conocimiento e identidad M0.1 (`data/Info_Models/*.txt` + Diálogos base)

Genera:
- data/corpus_sft/corpus_sft_1m.jsonl
"""

import json
import os
import re
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = str(REPO_ROOT / "data" / "corpus_sft")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "instrucciones_sft_conversaciones_1m_tokens.jsonl")
LEGACY_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "corpus_sft_1m.jsonl")

INSTRUCTION_BASE_M01 = [
    {
        "system": "Eres M0.1, una IA analítica con arquitectura MoE + MLA orientada al desarrollo de software y resolución de problemas.",
        "prompt": "¿Quién eres y cuál es tu propósito?",
        "response": "Hola, soy M0.1, un modelo de lenguaje con arquitectura de atención de espacio latente (MLA) y Mixture of Experts (MoE). Mi propósito es colaborar contigo de forma analítica, eficiente y precisa."
    },
    {
        "system": "Eres M0.1, una IA analítica con arquitectura MoE + MLA orientada al desarrollo de software y resolución de problemas.",
        "prompt": "¿Qué ventajas tiene tu arquitectura MoE?",
        "response": "La arquitectura Mixture of Experts (MoE) me permite activar únicamente un subconjunto de expertos (2 expertos activos + 1 experto compartido por token), manteniendo un bajo costo computacional y alta especialización por capa."
    },
    {
        "system": "Eres M0.1, un asistente técnico experto en desarrollo y arquitectura de software.",
        "prompt": "Explícame qué son los principios SOLID con un ejemplo simple.",
        "response": "Los principios SOLID son cinco reglas para diseñar software mantenible:\n1. S (Single Responsibility): Una clase debe tener una sola razón para cambiar.\n2. O (Open/Closed): Abierto para extensión, cerrado para modificación.\n3. L (Liskov Substitution): Las subclases deben poder sustituir a sus clases base.\n4. I (Interface Segregation): Interfaces pequeñas y específicas en lugar de monolíticas.\n5. D (Dependency Inversion): Depender de abstracciones, no de implementaciones concretas."
    }
]


def fetch_hf_rows(dataset_name: str, config: str = "default", split: str = "train", limit: int = 2000) -> list[dict]:
    """Descarga muestras limpias desde los servidores de Hugging Face mediante API REST."""
    print(f"[FETCH HF] Descargando hasta {limit} muestras de alta calidad desde '{dataset_name}'...")
    headers = {"User-Agent": "Mozilla/5.0"}
    offset = 0
    length = 100
    results = []

    while len(results) < limit:
        url = f"https://datasets-server.huggingface.co/rows?dataset={urllib.request.quote(dataset_name)}&config={config}&split={split}&offset={offset}&length={length}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read())
                rows = data.get("rows", [])
                if not rows:
                    break
                for r in rows:
                    row_data = r.get("row", {})
                    # Adaptador para FreedomIntelligence/evol-instruct-spanish
                    if "conversations" in row_data:
                        convs = row_data["conversations"]
                        if len(convs) >= 2 and convs[0].get("from") == "human" and convs[1].get("from") == "gpt":
                            results.append({
                                "prompt": convs[0]["value"].strip(),
                                "response": convs[1]["value"].strip()
                            })
                    # Adaptador para somosnlp/somos-clean-alpaca-es
                    elif "inputs" in row_data:
                        inputs = row_data["inputs"]
                        inst = inputs.get("1-instruction", "").strip()
                        inp = inputs.get("2-input", "").strip()
                        out = inputs.get("3-output", "").strip()
                        if inst and out:
                            p_text = f"{inst}\n\nContexto: {inp}" if inp else inst
                            results.append({
                                "prompt": p_text,
                                "response": out
                            })
                    if len(results) >= limit:
                        break
                offset += len(rows)
        except Exception as e:
            print(f"[WARNING] Fallo de red/desconexión parcial al consultar {dataset_name} en offset {offset}: {e}")
            break

    print(f"[FETCH HF] Obtenidas {len(results)} muestras limpias de {dataset_name}.")
    return results


def build_1m_sft_corpus():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_entries = []

    # 1. Muestras base M0.1
    for item in INSTRUCTION_BASE_M01:
        conv = f"<|user|>\n{item['prompt']}\n<|assistant|>\n{item['response']}"
        all_entries.append({
            "system": item["system"],
            "conversation": conv
        })

    # 2. Muestras de Razonamiento y Código (evol-instruct-spanish)
    evol_samples = fetch_hf_rows("FreedomIntelligence/evol-instruct-spanish", limit=1500)
    for sample in evol_samples:
        conv = f"<|user|>\n{sample['prompt']}\n<|assistant|>\n{sample['response']}"
        all_entries.append({
            "system": "Eres M0.1, un asistente técnico avanzado en programación, matemáticas y razonamiento.",
            "conversation": conv
        })

    # 3. Muestras Limpias de Instrucción (somos-clean-alpaca-es)
    alpaca_samples = fetch_hf_rows("somosnlp/somos-clean-alpaca-es", limit=1500)
    for sample in alpaca_samples:
        conv = f"<|user|>\n{sample['prompt']}\n<|assistant|>\n{sample['response']}"
        all_entries.append({
            "system": "Eres M0.1, un asistente amigable y analítico.",
            "conversation": conv
        })

    # 4. Muestras de destilación previas
    distill_path = str(REPO_ROOT / "archive" / "data" / "legacy" / "distillation" / "distill_qwen9b_20260718_1803_clean.jsonl")
    if os.path.exists(distill_path):
        with open(distill_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    all_entries.append({
                        "system": "Eres M0.1, un asistente especializado en razonamiento lógico y matemáticas.",
                        "conversation": data.get("text", f"<|user|>\n{data.get('prompt')}\n<|assistant|>\n{data.get('answer')}")
                    })

    # Escribir archivo JSONL unificado
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # Mantener enlace simbólico retrocompatible
    if os.path.islink(LEGACY_OUTPUT_FILE) or not os.path.exists(LEGACY_OUTPUT_FILE):
        if os.path.islink(LEGACY_OUTPUT_FILE):
            os.unlink(LEGACY_OUTPUT_FILE)
        os.symlink(os.path.basename(OUTPUT_FILE), LEGACY_OUTPUT_FILE)

    print(f"[CORPUS SFT 1M] ¡Guardadas {len(all_entries)} muestras de alta calidad en {OUTPUT_FILE}!")
    return OUTPUT_FILE


if __name__ == "__main__":
    build_1m_sft_corpus()
