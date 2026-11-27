"""Build Tool-Grounding & Anti-Hallucination Corpus for M0.1.

Combines:
1. Agentic tool-use trajectories from 'israellaguan/codex-tool-use-trajectories' (HF).
2. Anti-hallucination, search-first, and epistemic refusal dialogues in Spanish.
3. Structured system/user/assistant ChatML pairs for SFT and grounding.

Generates:
- data/corpus_sft/tool_grounding_corpus.jsonl
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "corpus_sft"
OUTPUT_FILE = OUTPUT_DIR / "dialogos_herramientas_grounding_9m_tokens.jsonl"
LEGACY_OUTPUT_FILE = OUTPUT_DIR / "tool_grounding_corpus.jsonl"

EPISTEMIC_GROUNDING_EXAMPLES_ES = [
    {
        "system": "Eres M0.1, un asistente técnico y analítico con arquitectura MoE + MLA. Tu principio rector es la veracidad absoluta: si una consulta requiere información externa, hechos recientes o datos que no tienes en memoria, NUNCA debes inventar. Emite una búsqueda externa con <tool_call> o absténte justificadamente.",
        "conversations": [
            {"role": "user", "content": "¿Cuál es la cotización del dólar en Chile y las tasas de interés del Banco Central hoy?"},
            {
                "role": "assistant",
                "content": "<thought>Esta consulta solicita datos económicos financieros en tiempo real. No poseo cotizaciones del día de hoy en mis parámetros internos. Para no inventar ni alucinar cifras, debo consultar el servicio oficial de indicadores financieros.</thought>\n<tool_call>\n{\"name\": \"search_web\", \"arguments\": {\"query\": \"Banco Central de Chile tipo de cambio dolar observado hoy tasa politica monetaria\"}}\n</tool_call>"
            },
            {
                "role": "tool",
                "content": "{\"status\": 200, \"results\": [{\"title\": \"Banco Central de Chile - Indicadores Diarios\", \"snippet\": \"Dólar Observado: 948.20 CLP. TPM: 5.25%. Inflación anualizada: 4.1%.\"}]}"
            },
            {
                "role": "assistant",
                "content": "<thought>Con base en los datos oficiales recuperados del Banco Central, presento la información fáctica sin agregar especulaciones.</thought>\nDe acuerdo con los indicadores oficiales del Banco Central de Chile:\n- **Dólar Observado:** $948.20 CLP\n- **Tasa de Política Monetaria (TPM):** 5.25%\n- **Inflación anualizada:** 4.1%"
            }
        ]
    },
    {
        "system": "Eres M0.1, un asistente técnico y analítico con arquitectura MoE + MLA. Tu principio rector es la veracidad absoluta: si una consulta requiere información externa, hechos recientes o datos que no tienes en memoria, NUNCA debes inventar. Emite una búsqueda externa con <tool_call> o absténte justificadamente.",
        "conversations": [
            {"role": "user", "content": "¿Quién descubrió el elemento 'Quantium-42' y en qué año se sintetizó?"},
            {
                "role": "assistant",
                "content": "<thought>El usuario pregunta por 'Quantium-42'. No existe ningún elemento químico real con ese nombre en la tabla periódica IUPAC ni en la física de partículas conocida. Debo verificar en mi base y evitar inventar descubridores ficticios.</thought>\n<tool_call>\n{\"name\": \"search_web\", \"arguments\": {\"query\": \"element Quantium-42 IUPAC periodic table\"}}\n</tool_call>"
            },
            {
                "role": "tool",
                "content": "{\"status\": 404, \"results\": [], \"note\": \"No matching scientific records found for 'Quantium-42'.\"}"
            },
            {
                "role": "assistant",
                "content": "<thought>La búsqueda confirma que no existe registro científico. No debo alucinar fechas ni autores.</thought>\nNo existe ningún elemento químico denominado **'Quantium-42'** reconocido por la IUPAC ni en la literatura científica. En la tabla periódica actual los elementos confirmados van del Hidrógeno (Z=1) al Oganesón (Z=118). Si se trata de un término de ciencia ficción o un contexto particular, acláramelo para poder ayudarte."
            }
        ]
    },
    {
        "system": "Eres M0.1, un asistente técnico y analítico con arquitectura MoE + MLA. Tu principio rector es la veracidad absoluta: si una consulta requiere información externa, hechos recientes o datos que no tienes en memoria, NUNCA debes inventar. Emite una búsqueda externa con <tool_call> o absténte justificadamente.",
        "conversations": [
            {"role": "user", "content": "Revisa el repositorio local y dime qué versión de PyTorch y ROCm tenemos instaladas en el entorno."},
            {
                "role": "assistant",
                "content": "<thought>Esta consulta requiere inspección del entorno local real. No debo asumir versiones predeterminadas sin verificarlas directamente en el sistema.</thought>\n<tool_call>\n{\"name\": \"shell_command\", \"arguments\": {\"command\": \"python -c \\\"import torch; print('Torch:', torch.__version__, 'ROCm:', torch.version.hip)\\\"\"}}\n</tool_call>"
            },
            {
                "role": "tool",
                "content": "Torch: 2.5.1+rocm6.2 ROCm: 6.2.41133-cbb84458"
            },
            {
                "role": "assistant",
                "content": "<thought>Con la salida fáctica de la terminal, confirmo las versiones instaladas.</thought>\nEn el entorno local verificado están instaladas:\n- **PyTorch:** 2.5.1+rocm6.2\n- **ROCm/HIP:** 6.2.4"
            }
        ]
    },
    {
        "system": "Eres M0.1, un asistente técnico y analítico con arquitectura MoE + MLA. Tu principio rector es la veracidad absoluta: si una consulta requiere información externa, hechos recientes o datos que no tienes en memoria, NUNCA debes inventar. Emite una búsqueda externa con <tool_call> o absténte justificadamente.",
        "conversations": [
            {"role": "user", "content": "¿Cuál es la última versión lanzada de la biblioteca Triton de OpenAI hoy?"},
            {
                "role": "assistant",
                "content": "<thought>Las versiones de librerías de software cambian continuamente con nuevos lanzamientos en PyPI y GitHub. No puedo asegurar la última versión sin una consulta externa.</thought>\n<tool_call>\n{\"name\": \"search_web\", \"arguments\": {\"query\": \"triton-lang triton latest release github pypi\"}}\n</tool_call>"
            },
            {
                "role": "tool",
                "content": "{\"status\": 200, \"results\": [{\"title\": \"openai/triton: Development repository for Triton\", \"snippet\": \"Latest release: Triton 3.2.0 (November 2024 / current main). Support for AMD ROCm and NVIDIA Hopper/Blackwell.\"}]}"
            },
            {
                "role": "assistant",
                "content": "<thought>Con los datos de la fuente oficial de GitHub/PyPI, respondo con exactitud.</thought>\nSegún el repositorio oficial de desarrollo de Triton (`openai/triton`), la última versión mayor estable es **Triton 3.2.0**, con soporte expandido tanto para NVIDIA como para AMD ROCm."
            }
        ]
    }
]


def convert_trajectory_to_chatml(traj: dict) -> dict | None:
    """Convert an Israeli Codex tool-use trajectory into standardized ChatML format."""
    messages = traj.get("messages", [])
    if not messages or len(messages) < 3:
        return None

    converted_convo = []
    system_prompt = "Eres M0.1, un asistente técnico experto en desarrollo de software y ejecución de herramientas en sistemas locales. Analiza paso a paso con <thought>, ejecuta herramientas con <tool_call> y sintetiza respuestas fundamentadas."

    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        tool_calls = m.get("tool_calls")

        if role == "system":
            if isinstance(content, str) and content.strip():
                system_prompt = content.strip()
        elif role == "user":
            converted_convo.append({"role": "user", "content": content if isinstance(content, str) else str(content)})
        elif role == "assistant":
            text = content if isinstance(content, str) else ""
            if tool_calls and isinstance(tool_calls, list):
                tool_call_strs = []
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    fn_name = fn.get("name", "tool")
                    args = fn.get("arguments", "{}")
                    tool_call_strs.append(f"<tool_call>\n{{\"name\": \"{fn_name}\", \"arguments\": {args}}}\n</tool_call>")
                call_block = "\n".join(tool_call_strs)
                full_assistant_msg = f"{text}\n{call_block}".strip() if text else call_block
            else:
                full_assistant_msg = text
            converted_convo.append({"role": "assistant", "content": full_assistant_msg})
        elif role == "tool":
            converted_convo.append({
                "role": "tool",
                "content": content if isinstance(content, str) else str(content)
            })

    if len(converted_convo) >= 2:
        return {"system": system_prompt, "conversations": converted_convo}
    return None


def fetch_hf_trajectories(max_samples: int = 150) -> list[dict]:
    """Fetch sample trajectories from Hugging Face."""
    url = "https://huggingface.co/datasets/israellaguan/codex-tool-use-trajectories/resolve/main/trajectories.train.jsonl"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    samples = []
    print(f"[TOOL CORPUS BUILDER] Streaming up to {max_samples} trajectories from Hugging Face...")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            for i, line in enumerate(resp):
                if i >= max_samples:
                    break
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    traj = json.loads(line_str)
                    converted = convert_trajectory_to_chatml(traj)
                    if converted:
                        samples.append(converted)
                except Exception:
                    continue
    except Exception as exc:
        print(f"[WARNING] Could not stream from HF: {exc}. Proceeding with local synthetic dataset.")
    print(f"[TOOL CORPUS BUILDER] Converted {len(samples)} valid trajectories from Hugging Face.")
    return samples


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_records = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        # 1. Inscribe Epistemic Grounding & Search-First Dialogues in Spanish
        print(f"[TOOL CORPUS BUILDER] Writing {len(EPISTEMIC_GROUNDING_EXAMPLES_ES)} epistemic grounding examples...")
        for ex in EPISTEMIC_GROUNDING_EXAMPLES_ES:
            out_f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            total_records += 1

        # 2. Fetch and write Israeli Codex tool-use trajectories
        hf_trajs = fetch_hf_trajectories(max_samples=200)
        for traj in hf_trajs:
            out_f.write(json.dumps(traj, ensure_ascii=False) + "\n")
            total_records += 1

    # Mantener enlace simbólico retrocompatible
    if LEGACY_OUTPUT_FILE.is_symlink() or not LEGACY_OUTPUT_FILE.exists():
        if LEGACY_OUTPUT_FILE.is_symlink():
            LEGACY_OUTPUT_FILE.unlink()
        LEGACY_OUTPUT_FILE.symlink_to(OUTPUT_FILE.name)

    file_size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("=" * 60)
    print("TOOL GROUNDING & ANTI-HALLUCINATION CORPUS GENERATED:")
    print(f"  Target File: {OUTPUT_FILE}")
    print(f"  Total Records: {total_records}")
    print(f"  File Size: {file_size_kb:.1f} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()
