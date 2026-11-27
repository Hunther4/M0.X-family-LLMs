"""Tests unitarios para Fill-In-The-Middle (FIM) y Modo Razonamiento (ON/OFF)."""

import os
import pytest
import torch
from torch.utils.data import DataLoader

from src.tokenizer.bpe import Tokenizer
from src.training.fim import (
    fim_split,
    format_fim,
    build_fim_prompt,
    build_chat_prompt,
    format_training_turn,
    FIMCodeDataset,
    FIM_PREFIX,
    FIM_SUFFIX,
    FIM_MIDDLE,
    THINK_START,
    THINK_END,
    USER_START,
    ASSISTANT_START,
)


@pytest.fixture
def tokenizer():
    tok = Tokenizer()
    tok_path = os.path.join("data", "tokenizers", "tokenizer.json")
    if os.path.exists(tok_path):
        tok.load(tok_path)
    return tok


def test_fim_split_reconstruction():
    code = """public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}"""
    p, m, s = fim_split(code, seed=42)
    assert p + m + s == code
    assert len(p) > 0
    assert len(m) > 0
    assert len(s) > 0


def test_format_fim_psm_and_spm():
    p, m, s = "public int ", "add(int a, int b) ", "{ return a + b; }"
    psm = format_fim(p, m, s, mode="PSM")
    assert psm.startswith(FIM_PREFIX)
    assert FIM_SUFFIX in psm
    assert FIM_MIDDLE in psm
    assert psm.endswith("<|endoftext|>")

    spm = format_fim(p, m, s, mode="SPM")
    assert spm.startswith(FIM_SUFFIX)
    assert FIM_PREFIX in spm
    assert FIM_MIDDLE in spm


def test_build_fim_prompt_inference():
    prefix = "def calculate_area(width, height):\n    "
    suffix = "\n    return area"
    prompt = build_fim_prompt(prefix, suffix, mode="PSM")
    assert prompt == f"{FIM_PREFIX}{prefix}{FIM_SUFFIX}{suffix}{FIM_MIDDLE}"


def test_chat_prompt_reasoning_mode_toggle():
    user_q = "¿Cuál es la complejidad de QuickSort?"
    
    # Modo ACTIVO (ON) -> Debe incluir etiqueta y terminar en <|think|>\n
    prompt_on = build_chat_prompt(user_q, reasoning_mode=True, system_prompt="Eres un asistente experto.")
    assert "[MODO_RAZONAMIENTO: ACTIVO]" in prompt_on
    assert prompt_on.endswith(f"{THINK_START}\n")
    assert ASSISTANT_START not in prompt_on

    # Modo DESACTIVADO (OFF) -> Debe terminar en <|assistant|>\n y no abrir <|think|>
    prompt_off = build_chat_prompt(user_q, reasoning_mode=False, system_prompt="Eres un asistente experto.")
    assert "[MODO_RAZONAMIENTO: DESACTIVADO]" in prompt_off
    assert prompt_off.endswith(f"{ASSISTANT_START}\n")
    assert THINK_START not in prompt_off


def test_format_training_turn_with_and_without_thinking():
    # Caso 1: Con traza de pensamiento (Razonamiento ACTIVO)
    turn_think = format_training_turn(
        user_message="2 + 2?",
        assistant_response="4",
        thinking_trace="El usuario suma dos números enteros básicos.",
    )
    assert THINK_START in turn_think
    assert THINK_END in turn_think
    assert "El usuario suma" in turn_think
    assert turn_think.endswith("<|endoftext|>")

    # Caso 2: Sin traza de pensamiento (Razonamiento DESACTIVADO)
    turn_direct = format_training_turn(
        user_message="Hola",
        assistant_response="Hola, ¿en qué puedo ayudarte?",
        thinking_trace=None,
    )
    assert THINK_START not in turn_direct
    assert THINK_END not in turn_direct
    assert ASSISTANT_START in turn_direct


def test_fim_code_dataset_integration(tokenizer):
    samples = [
        "void main() { System.out.println(\"Hello 1\"); }",
        "int square(int x) { return x * x; }",
        "record Point(int x, int y) {}",
    ]
    ds = FIMCodeDataset(tokenizer, samples, fim_rate=1.0, seq_len=32)
    assert len(ds) > 0
    x, y = ds[0]
    assert x.shape == (32,)
    assert y.shape == (32,)
    assert torch.equal(x[1:], y[:-1])
