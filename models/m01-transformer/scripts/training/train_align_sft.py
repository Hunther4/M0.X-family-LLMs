"""Script de Alineación Instructiva Rápida (Fine-Tuning con Loss Masking Puro).

Aplica 100 pasos de alineación sobre data/corpus_sft/corpus_sft_1m.jsonl utilizando
el checkpoint de wiki-python (5,778 pasos acumulados) para fijar el formato de respuesta instructiva.

Uso:
  python -m scripts.training.train_align_sft
"""

import os
import sys
import torch
from torch.utils.data import DataLoader

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.tokenizer.bpe import Tokenizer
from src.training.config import TrainingConfig
from src.training.datasets import JsonlDataset
from src.training.train import configure_optimizer, get_lr_scheduler, worker_init_fn
from src.engine_v2.engine import TrainingEngineV2
from src.engine_v2.experiment import ExperimentManager

CHECKPOINT_BASE = "runs/run_sft_wiki_python_b6/checkpoints/checkpoint.pt"
SFT_CORPUS = (
    "data/corpus_sft/instrucciones_sft_conversaciones_1m_tokens.jsonl"
    if os.path.exists("data/corpus_sft/instrucciones_sft_conversaciones_1m_tokens.jsonl")
    else "data/corpus_sft/corpus_sft_1m.jsonl"
)
RUN_NAME = "run_sft_alignment_final"
MAX_STEPS = 100
BATCH_SIZE = 4
GRAD_ACCUM_STEPS = 2


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[ALINEACIÓN SFT] Ejecutando en dispositivo: {device}")

    # 1. Tokenizer
    tokenizer_path = os.path.join("data", "tokenizers", "tokenizer.json")
    tokenizer = Tokenizer()
    if os.path.exists(tokenizer_path):
        print(f"[ALINEACIÓN SFT] Cargando Tokenizer de 16k desde {tokenizer_path}...")
        tokenizer.load(tokenizer_path)

    # 2. Config & Modelo
    model_config = M01Config(vocab_size=16384)
    model = TransformerLM(model_config)

    # 3. Dataset Instructivo (corpus_sft_1m.jsonl)
    print(f"[ALINEACIÓN SFT] Cargando dataset de alineación desde {SFT_CORPUS}...")
    align_ds = JsonlDataset(
        tokenizer=tokenizer,
        paths=[SFT_CORPUS],
        seq_len=1024,
        max_lines_per_shard=10_000
    )

    # En WSL2 y ROCm, num_workers=0 previene duplicación de RAM y cuelgues del driver Direct3D
    num_workers = 0
    persistent_workers = False

    train_loader = DataLoader(
        align_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        drop_last=True,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
        persistent_workers=persistent_workers,
        prefetch_factor=None,
        worker_init_fn=worker_init_fn,
    )

    train_config = TrainingConfig(
        batch_size=BATCH_SIZE,
        seq_len=1024,
        max_lr=8.0e-5,
        min_lr_ratio=0.1,
        warmup_steps=10,
        max_steps=MAX_STEPS,
        weight_decay=0.01,
        max_norm=1.0,
        log_interval=10,
        save_interval=50,
        val_interval=500,
    )

    optimizer = configure_optimizer(model, train_config)
    scheduler = get_lr_scheduler(
        optimizer,
        warmup_steps=train_config.warmup_steps,
        max_steps=train_config.max_steps,
        min_lr_ratio=train_config.min_lr_ratio,
    )

    experiment_mgr = ExperimentManager(base_dir="runs", run_name=RUN_NAME)

    engine = TrainingEngineV2(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        train_loader=train_loader,
        val_loader=None,
        config=train_config,
        experiment_manager=experiment_mgr,
        gradient_accumulation_steps=GRAD_ACCUM_STEPS,
        max_norm=train_config.max_norm,
        device=device,
    )

    if os.path.exists(CHECKPOINT_BASE):
        print(f"[ALINEACIÓN SFT] Cargar pesos del checkpoint 5,778 pasos desde: {CHECKPOINT_BASE}")
        engine.resume(CHECKPOINT_BASE)

    print(f"[ALINEACIÓN SFT] ¡Iniciando alineación por {MAX_STEPS} pasos a Batch {BATCH_SIZE}!")
    engine.fit(max_steps=MAX_STEPS)
    print(f"[ALINEACIÓN SFT] ¡Alineación completada! Guardado en runs/{RUN_NAME}/checkpoints/")


if __name__ == "__main__":
    main()
