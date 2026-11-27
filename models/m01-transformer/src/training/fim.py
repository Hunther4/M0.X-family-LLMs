"""Módulo de Transformación Fill-In-The-Middle (FIM) y Control de Modo Razonamiento (ON/OFF).

Diseñado para M0.1 Transformer:
1. Autocompletado de código asistido por contexto previo y posterior (FIM).
   Formato estándar PSM (Prefix-Suffix-Middle) y SPM (Suffix-Prefix-Middle).
2. Modo Razonamiento Binario (Activo / Desactivado):
   - ACTIVO (ON): Emite <|think|> ... razonamiento ... <|/think|> antes de responder.
   - DESACTIVADO (OFF): Emite directamente <|assistant|> ... respuesta directa/código.
"""

import random
from typing import Dict, List, Optional, Tuple, Union
import torch
from torch.utils.data import Dataset

# Tokens canónicos FIM y Razonamiento para M0.1
FIM_PREFIX = "<|fim_prefix|>"
FIM_SUFFIX = "<|fim_suffix|>"
FIM_MIDDLE = "<|fim_middle|>"
EOS_TOKEN = "<|endoftext|>"

THINK_START = "<|think|>"
THINK_END = "<|/think|>"
USER_START = "<|user|>"
ASSISTANT_START = "<|assistant|>"


# =====================================================================
# 1. Transformación Fill-In-The-Middle (FIM)
# =====================================================================

def fim_split(
    text: str,
    p_prefix: float = 0.5,
    seed: Optional[int] = None,
) -> Tuple[str, str, str]:
    """Divide un documento de código en tres fragmentos: Prefijo, Medio y Sufijo.

    Args:
        text: Código fuente o documento.
        p_prefix: Punto medio objetivo de división (usado como referencia de distribución).
        seed: Semilla opcional para reproducibilidad.

    Returns:
        Tupla (prefijo, medio, sufijo).
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random

    n = len(text)
    if n < 3:
        return text, "", ""

    # Elegir dos puntos de corte ordenados
    # Se favorecen límites de línea para preservar coherencia sintáctica cuando sea posible
    lines = text.splitlines(keepends=True)
    if len(lines) >= 3:
        i_line = rng.randint(1, max(1, len(lines) - 2))
        j_line = rng.randint(i_line + 1, len(lines) - 1)
        prefix = "".join(lines[:i_line])
        middle = "".join(lines[i_line:j_line])
        suffix = "".join(lines[j_line:])
    else:
        idx1 = rng.randint(1, n - 2)
        idx2 = rng.randint(idx1 + 1, n - 1)
        prefix = text[:idx1]
        middle = text[idx1:idx2]
        suffix = text[idx2:]

    return prefix, middle, suffix


def format_fim(
    prefix: str,
    middle: str,
    suffix: str,
    mode: str = "PSM",
) -> str:
    """Empaqueta los fragmentos en el formato FIM correspondiente.

    Modos soportados:
    - PSM (Prefix-Suffix-Middle):
      <|fim_prefix|>P<|fim_suffix|>S<|fim_middle|>M<|endoftext|>
    - SPM (Suffix-Prefix-Middle):
      <|fim_suffix|>S<|fim_prefix|>P<|fim_middle|>M<|endoftext|>

    Args:
        prefix: Lo que está antes del cursor en el editor.
        middle: Lo que se debe predecir en la posición del cursor.
        suffix: Lo que está después del cursor en el editor.
        mode: "PSM" o "SPM" (por omisión "PSM").
    """
    mode = mode.upper()
    if mode == "PSM":
        return f"{FIM_PREFIX}{prefix}{FIM_SUFFIX}{suffix}{FIM_MIDDLE}{middle}{EOS_TOKEN}"
    elif mode == "SPM":
        return f"{FIM_SUFFIX}{suffix}{FIM_PREFIX}{prefix}{FIM_MIDDLE}{middle}{EOS_TOKEN}"
    else:
        raise ValueError(f"Modo FIM no reconocido: {mode}. Debe ser 'PSM' o 'SPM'.")


def build_fim_prompt(prefix: str, suffix: str, mode: str = "PSM") -> str:
    """Construye el prompt de inferencia para autocompletar código en el cursor.

    En el IDE/editor:
    prompt = build_fim_prompt(codigo_antes, codigo_despues)
    El modelo genera el código faltante hasta encontrar <|endoftext|>.
    """
    mode = mode.upper()
    if mode == "PSM":
        return f"{FIM_PREFIX}{prefix}{FIM_SUFFIX}{suffix}{FIM_MIDDLE}"
    elif mode == "SPM":
        return f"{FIM_SUFFIX}{suffix}{FIM_PREFIX}{prefix}{FIM_MIDDLE}"
    else:
        raise ValueError(f"Modo FIM no soportado: {mode}")


# =====================================================================
# 2. Control de Modo Razonamiento (ACTIVO / DESACTIVADO)
# =====================================================================

def build_chat_prompt(
    user_message: str,
    reasoning_mode: bool = False,
    system_prompt: Optional[str] = None,
) -> str:
    """Construye el prompt de entrada para el modelo con selector de razonamiento.

    Args:
        user_message: Consulta o instrucción del usuario.
        reasoning_mode:
            - True (ACTIVO): Fuerza al modelo a abrir <|think|> y razonar paso a paso.
            - False (DESACTIVADO): Lleva al modelo directamente a <|assistant|> para respuesta inmediata.
        system_prompt: Mensaje del sistema opcional.

    Returns:
        Cadena formateada lista para alimentar el modelo.
    """
    parts = []
    if system_prompt:
        mode_tag = "[MODO_RAZONAMIENTO: ACTIVO]" if reasoning_mode else "[MODO_RAZONAMIENTO: DESACTIVADO]"
        parts.append(f"{system_prompt} {mode_tag}\n")

    parts.append(f"{USER_START}\n{user_message.strip()}\n")

    if reasoning_mode:
        # Modo ACTIVO: el prompt se pre-llena con <|think|>\n obligando al modelo a pensar
        parts.append(f"{THINK_START}\n")
    else:
        # Modo DESACTIVADO: el prompt se pre-llena con <|assistant|>\n y responde de inmediato
        parts.append(f"{ASSISTANT_START}\n")

    return "".join(parts)


def format_training_turn(
    user_message: str,
    assistant_response: str,
    thinking_trace: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """Empaqueta una muestra para entrenamiento supervisado respetando el modo de razonamiento.

    Si thinking_trace está presente y no vacío -> Muestra con Razonamiento ACTIVO.
    Si thinking_trace es None o vacío -> Muestra con Razonamiento DESACTIVADO.
    """
    has_thinking = bool(thinking_trace and thinking_trace.strip())
    parts = []
    if system_prompt:
        mode_tag = "[MODO_RAZONAMIENTO: ACTIVO]" if has_thinking else "[MODO_RAZONAMIENTO: DESACTIVADO]"
        parts.append(f"{system_prompt} {mode_tag}\n")

    parts.append(f"{USER_START}\n{user_message.strip()}\n")

    if has_thinking:
        parts.append(f"{THINK_START}\n{thinking_trace.strip()}\n{THINK_END}\n")

    parts.append(f"{ASSISTANT_START}\n{assistant_response.strip()}\n{EOS_TOKEN}")
    return "".join(parts)


# =====================================================================
# 3. Dataset FIM & Multi-Task con Longitud Dinámica (hasta 32k)
# =====================================================================

class FIMCodeDataset(Dataset):
    """Dataset de código con aumento dinámico Fill-In-The-Middle (FIM).

    Args:
        tokenizer: Tokenizador M0.1.
        code_samples: Lista de fragmentos de código o archivos.
        fim_rate: Probabilidad de aplicar FIM a una muestra (0.0 = código puro, 0.5 = mitad FIM, 1.0 = todo FIM).
        psm_rate: Probabilidad de usar formato PSM vs SPM para muestras FIM (default 0.8 PSM).
        seq_len: Longitud de la ventana deslizante (ej: 1024, 2048, 4096...).
    """

    def __init__(
        self,
        tokenizer,
        code_samples: List[str],
        fim_rate: float = 0.5,
        psm_rate: float = 0.8,
        seq_len: int = 1024,
    ):
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.fim_rate = fim_rate
        self.psm_rate = psm_rate

        all_tokens: List[int] = []
        for sample in code_samples:
            if not sample or not sample.strip():
                continue

            if random.random() < self.fim_rate:
                p, m, s = fim_split(sample)
                mode = "PSM" if random.random() < self.psm_rate else "SPM"
                formatted_text = format_fim(p, m, s, mode=mode)
            else:
                formatted_text = f"{sample.strip()}\n{EOS_TOKEN}"

            tokens = tokenizer.encode(formatted_text)
            all_tokens.extend(tokens)

        self.tokens = torch.tensor(all_tokens, dtype=torch.long)
        self.total_tokens = len(self.tokens)

    def __len__(self) -> int:
        if self.total_tokens <= self.seq_len:
            return 0
        return self.total_tokens - self.seq_len

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        start = idx
        end = start + self.seq_len
        x = self.tokens[start:end]
        y = self.tokens[start + 1 : end + 1]
        return x, y
