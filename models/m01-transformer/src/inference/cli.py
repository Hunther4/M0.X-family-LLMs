"""CLI entry point for text generation.

Usage:
    python -m src.inference.cli --prompt "Hello world"
    python -m src.inference.cli --prompt "Once upon a time" --max-len 200 --temperature 0.8 --top-k 50
"""

import argparse
import os
import sys

import torch

from src.inference.generate import generate
from src.model.lm import TransformerLM
from src.tokenizer.bpe import Tokenizer
from src.transformer.config import M01Config
from src.engine_v2.checkpoint_v2 import normalize_checkpoint_state
from src.engine_v2.checkpoint_v2 import safe_load_checkpoint


def format_chat_prompt(raw_prompt: str) -> str:
    """Wrap plain-text input in chat template tags if not already present.

    This lets users pass a bare question without manually typing
    ``<|user|>`` and ``<|assistant|>`` every time.

    Example:
        Input:  "¿Qué son los principios SOLID?"
        Output: "<|user|>\\n¿Qué son los principios SOLID?\\n<|assistant|>\\n"
    """
    if "<|user|>" not in raw_prompt:
        return f"<|user|>\n{raw_prompt.strip()}\n<|assistant|>\n"
    return raw_prompt


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate text with the M0.1 transformer model.",
    )
    parser.add_argument(
        "--prompt", type=str, default="Hola",
        help="Input prompt text. Plain text is auto-wrapped in chat tags (default: 'Hola')",
    )
    parser.add_argument(
        "--checkpoint", type=str,
        default="runs/run_sft_m01/checkpoints/checkpoint.pt",
        help="Path to model checkpoint (default: runs/run_sft_m01/checkpoints/checkpoint.pt)",
    )
    parser.add_argument(
        "--max-len", type=int, default=100,
        help="Maximum number of new tokens to generate (default: 100)",
    )
    parser.add_argument(
        "--temperature", type=float, default=1.0,
        help="Sampling temperature. 0 = greedy (default: 1.0)",
    )
    parser.add_argument(
        "--top-k", type=int, default=None,
        help="Top-k sampling threshold (default: disabled)",
    )
    parser.add_argument(
        "--top-p", type=float, default=None,
        help="Nucleus sampling threshold, e.g. 0.9 (default: disabled)",
    )
    parser.add_argument(
        "--device", type=str, default="auto",
        help='Device: "auto" (detect), "cuda", or "cpu" (default: auto)',
    )
    return parser.parse_args(argv)


def resolve_device(device_arg: str) -> torch.device:
    """Resolve device string to torch.device."""
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args(argv or sys.argv[1:])
    device = resolve_device(args.device)

    print(f"Device: {device}")
    print(f"Loading checkpoint: {args.checkpoint}")

    # Load trained weights and architecture metadata from checkpoint.
    state = safe_load_checkpoint(args.checkpoint, map_location=device)
    state = normalize_checkpoint_state(state, require_architecture=True)
    config_dict = state["model_config"]
    valid_fields = set(M01Config.__dataclass_fields__)
    config = M01Config(**{k: v for k, v in config_dict.items() if k in valid_fields})
    model = TransformerLM(config).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()
    print(f"Loaded step {state.get('step', 0)}, loss {state.get('loss', 'N/A')}")

    tokenizer = Tokenizer()
    tok_json = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tokenizers", "tokenizer.json")
    if os.path.exists(tok_json):
        tokenizer.load(tok_json)

    # Auto-wrap plain prompts so users don't need to type tags manually.
    prompt = format_chat_prompt(args.prompt)
    print(f"\nPrompt: {prompt}")
    print("Generating...\n")

    output = generate(
        model=model,
        tokenizer=tokenizer,
        prompt=prompt,
        max_gen_len=args.max_len,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        device=device,
    )

    print(output)
    print()


if __name__ == "__main__":
    main()
