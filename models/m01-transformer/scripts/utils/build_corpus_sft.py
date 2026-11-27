"""Script para construir el Corpus SFT unificado de M0.1.

Procesa:
1. Documentos teóricos en data/Info_Models/*.txt
2. Un conjunto ampliado de diálogos instructivos y de razonamiento en español.

Genera:
- data/corpus_sft/corpus_sft.jsonl
"""

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = str(REPO_ROOT / "data" / "corpus_sft")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "instrucciones_sft_asistente_45k_tokens.jsonl")
LEGACY_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "corpus_sft.jsonl")

INSTRUCTION_DATASETS_ES = [
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
    },
    {
        "system": "Eres M0.1, un asistente técnico experto en Python y optimización.",
        "prompt": "¿Cómo funciona np.memmap y por qué ayuda a reducir el uso de RAM?",
        "response": "np.memmap mapea un archivo en disco directamente al espacio de direcciones virtuales del proceso sin cargar todo el contenido a la memoria RAM de golpe. Los datos se leen desde el disco a demanda mediante paginación del sistema operativo, reduciendo el consumo de RAM hasta en un 75%."
    },
    {
        "system": "Eres M0.1, un asistente amigable y profesional.",
        "prompt": "¿Cómo puedo empezar un proyecto con arquitectura limpia?",
        "response": "Para empezar con Arquitectura Limpia (Clean Architecture):\n1. Separa las entidades de dominio centrales de las dependencias externas.\n2. Define puertos (interfaces) para la entrada y salida de datos.\n3. Implementa adaptadores para bases de datos, APIs o UIs sin contaminar la lógica central."
    }
]


def extract_qa_from_text(text: str, filename: str) -> list[dict]:
    """Extrae bloques de conocimiento de archivos .txt y los convierte a pares instrucción/respuesta."""
    sections = re.split(r'\n(?=##?\s+)', text)
    extracted = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        lines = sec.split('\n')
        title = lines[0].replace('#', '').strip()
        body = '\n'.join(lines[1:]).strip()

        if len(body) > 50:
            extracted.append({
                "system": "Eres M0.1, un asistente analítico especializado en conocimiento técnico y fundamentos de ingeniería.",
                "prompt": f"Explica en detalle el concepto de: {title}",
                "response": body
            })
    return extracted


def build_corpus_sft():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_entries = []

    # A. Agregar diálogos instructivos base
    for item in INSTRUCTION_DATASETS_ES:
        conv_formatted = f"<|user|>\n{item['prompt']}\n<|assistant|>\n{item['response']}"
        all_entries.append({
            "system": item["system"],
            "conversation": conv_formatted
        })

    # B. Agregar muestras de razonamiento/SFT destiladas (Qwen 9B en español)
    distill_path = str(REPO_ROOT / "archive" / "data" / "legacy" / "distillation" / "distill_qwen9b_20260718_1803_clean.jsonl")
    if os.path.exists(distill_path):
        print(f"[CORPUS SFT] Leyendo dataset de destilación/razonamiento en español desde {distill_path}...")
        with open(distill_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                all_entries.append({
                    "system": "Eres M0.1, un asistente amigable especializado en razonamiento lógico, matemáticas y desarrollo.",
                    "conversation": data.get("text", f"<|user|>\n{data.get('prompt')}\n<|assistant|>\n{data.get('answer')}")
                })

    # C. Procesar todos los archivos .txt de data/Info_Models/ si existen
    info_models_dir = str(REPO_ROOT / "data" / "Info_Models")
    if os.path.exists(info_models_dir):
        txt_files = [f for f in os.listdir(info_models_dir) if f.endswith('.txt')]
        print(f"[CORPUS SFT] Procesando {len(txt_files)} archivos .txt desde {info_models_dir}...")
        for fname in txt_files:
            fpath = os.path.join(info_models_dir, fname)
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                qa_list = extract_qa_from_text(content, fname)
                for item in qa_list:
                    conv_formatted = f"<|user|>\n{item['prompt']}\n<|assistant|>\n{item['response']}"
                    all_entries.append({
                        "system": item["system"],
                        "conversation": conv_formatted
                    })

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entry in all_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    # Mantener enlace simbólico retrocompatible
    if os.path.islink(LEGACY_OUTPUT_FILE) or not os.path.exists(LEGACY_OUTPUT_FILE):
        if os.path.islink(LEGACY_OUTPUT_FILE):
            os.unlink(LEGACY_OUTPUT_FILE)
        os.symlink(os.path.basename(OUTPUT_FILE), LEGACY_OUTPUT_FILE)

    print(f"[CORPUS SFT] ¡Construcción exitosa! Se generaron {len(all_entries)} muestras de entrenamiento SFT en {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    build_corpus_sft()
