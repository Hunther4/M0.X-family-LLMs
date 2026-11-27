"""CLI Entry Point for the M0.1 Research Framework V2 (TrainingEngineV2).

Enterprise-Grade LLM Training Suite with:
- Optimizers: EnterpriseHybridOptimizer (Muon for 2D weights + AdamW for 1D/embeddings) and pure AdamW.
- Schedulers: WSD (Warmup-Stable-Decay, SOTA DeepSeek/Llama) and Cosine Annealing.
- Dataset: Non-overlapping block chunked binary shards (>u2 uint16 big-endian).
"""

import argparse
import os
import sys
import math
import time
from dataclasses import fields
try:
    import psutil
except ImportError:
    psutil = None

import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
from torch.utils.data import DataLoader

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.transformer.fp8_linear import apply_fp8_linear
from src.training.config import TrainingConfig
from src.training.dataset import TinyShakespeareDataset, BinaryCorpusDataset
from src.training.optimizer import EnterpriseHybridOptimizer
from src.training.scheduler import get_wsd_schedule, get_cosine_with_warmup_schedule
from src.engine_v2.engine import TrainingEngineV2, get_cuda_memory_metrics_mb
from src.engine_v2.experiment import ExperimentManager


def configure_optimizer(
    model: torch.nn.Module,
    config: TrainingConfig,
    optimizer_type: str | None = None,
    muon_lr: float | None = None,
):
    """Configura optimizador empresarial (Muon + AdamW o AdamW clásico)."""
    opt_type = optimizer_type or getattr(config, "optimizer", "adamw")
    if opt_type == "hybrid_muon":
        m_lr = muon_lr if muon_lr is not None else getattr(config, "muon_lr", 0.02)
        return EnterpriseHybridOptimizer(
            model=model,
            muon_lr=m_lr,
            adamw_lr=config.max_lr,
            muon_weight_decay=0.01,
            adamw_weight_decay=config.weight_decay,
            adamw_betas=(config.beta1, config.beta2),
        )

    # Pure AdamW fallback (2 param groups: decay and no_decay)
    decay: list[torch.nn.Parameter] = []
    no_decay: list[torch.nn.Parameter] = []

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if "bias" in name or "gamma" in name or "norm" in name:
            no_decay.append(param)
        else:
            decay.append(param)

    all_params = decay + no_decay
    all_cuda = (
        torch.cuda.is_available()
        and bool(all_params)
        and all(p.is_cuda for p in all_params)
    )
    use_fused = all_cuda and "fused" in AdamW.__init__.__code__.co_varnames
    return AdamW(
        [
            {"params": decay, "weight_decay": config.weight_decay},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=config.max_lr,
        betas=(config.beta1, config.beta2),
        eps=1e-8,
        fused=use_fused,
    )


def get_lr_scheduler(
    optimizer,
    warmup_steps: int,
    max_steps: int,
    min_lr_ratio: float = 0.1,
    scheduler_type: str = "wsd",
    stable_ratio: float = 0.8,
) -> LambdaLR:
    """Configura el planificador de tasa de aprendizaje (WSD o Cosine)."""
    if scheduler_type == "wsd":
        return get_wsd_schedule(
            optimizer=optimizer,
            warmup_steps=warmup_steps,
            max_steps=max_steps,
            stable_ratio=stable_ratio,
            min_lr_ratio=min_lr_ratio,
        )

    return get_cosine_with_warmup_schedule(
        optimizer=optimizer,
        warmup_steps=warmup_steps,
        max_steps=max_steps,
        min_lr_ratio=min_lr_ratio,
    )


def worker_init_fn(worker_id: int) -> None:
    import numpy as np
    import random
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)


def build_training_dataset(config: TrainingConfig, corpus_dir: str | None = None, load_to_ram: bool = False):
    """Build a BinaryCorpusDataset or fall back to TinyShakespeareDataset."""
    if corpus_dir is None:
        corpus_dir = os.path.join(
            config.data_dir, "corpus", "corpus2_es_wiki_gutenberg_17M"
        )
    if os.path.isdir(corpus_dir):
        try:
            return BinaryCorpusDataset(config, corpus_dir, load_to_ram=load_to_ram)
        except (FileNotFoundError, ValueError, OSError) as exc:
            raise RuntimeError(
                f"Canonical corpus exists but is unusable: {corpus_dir}. "
                "Repair its shard_*.bin files instead of falling back to TinyShakespeare."
            ) from exc
    return TinyShakespeareDataset(config)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train M0.1 Transformer with Enterprise Training Suite.")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to YAML config file. CLI flags override YAML values.")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--corpus-dir", type=str, default=None,
                        help="Explicit path to binary corpus shards (e.g. LLM_DATASETS/TOKENIZED/corpus_expanded_v1).")
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--seq-len", type=int, default=None)
    parser.add_argument("--max-lr", type=float, default=None)
    parser.add_argument("--muon-lr", type=float, default=None, help="Learning rate for Muon 2D weight optimizer (default: 0.02).")
    parser.add_argument("--optimizer", type=str, choices=["hybrid_muon", "adamw"], default=None,
                        help="Optimizer type: 'hybrid_muon' (Muon + AdamW) or 'adamw'.")
    parser.add_argument("--scheduler", type=str, choices=["wsd", "cosine"], default=None,
                        help="LR Scheduler type: 'wsd' (Warmup-Stable-Decay) or 'cosine'.")
    parser.add_argument("--stable-ratio", type=float, default=None,
                        help="WSD stable phase ratio (default: 0.8 = 80% steps in warmup+stable).")
    parser.add_argument("--min-lr-ratio", type=float, default=None)
    parser.add_argument("--warmup-steps", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--weight-decay", type=float, default=None)
    parser.add_argument("--grad-accum-steps", type=int, default=None)
    parser.add_argument("--max-norm", type=float, default=None)
    parser.add_argument("--log-interval", type=int, default=None)
    parser.add_argument("--save-interval", type=int, default=None)
    parser.add_argument("--val-interval", type=int, default=None)
    parser.add_argument("--resume", nargs="?", const="__canonical__", default=None,
                        help="Resume training from canonical checkpoint or explicit path.")
    parser.add_argument("--vocab-size", type=int, default=None, help="Model vocab size (must match tokenizer; 16384 = canonical 16k)")
    parser.add_argument("--run-name", type=str, default=None,
                        help="Pin the run directory name under runs/ (e.g. run_enterprise_v1).")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda", "dml"],
                        help="Target compute device: 'auto' (default: cuda > dml > cpu), 'cpu', 'cuda', 'dml'.")
    parser.add_argument("--fp8", action="store_true", default=False,
                        help="Enable FP8 training for attention/MoE Linear layers (RDNA4 ROCm native, no-op if unsupported).")
    parser.add_argument("--load-to-ram", dest="load_to_ram", action="store_true", default=True,
                        help="Preload entire corpus into RAM (default: True).")
    parser.add_argument("--no-ram", dest="load_to_ram", action="store_false",
                        help="Do not load entire corpus into RAM; use memory mapping instead.")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args(sys.argv[1:])

    # --- Build configs: YAML base → CLI overrides → dataclass defaults ---
    if args.config:
        train_config = TrainingConfig.from_yaml(args.config)
    else:
        train_config = TrainingConfig()

    _TRAIN_CLI_MAP = {
        "batch_size": args.batch_size,
        "seq_len": args.seq_len,
        "max_lr": args.max_lr,
        "min_lr_ratio": args.min_lr_ratio,
        "warmup_steps": args.warmup_steps,
        "max_steps": args.max_steps,
        "weight_decay": args.weight_decay,
        "grad_accum_steps": args.grad_accum_steps,
        "max_norm": args.max_norm,
        "log_interval": args.log_interval,
        "save_interval": args.save_interval,
        "val_interval": args.val_interval,
        "data_dir": args.data_dir,
        "optimizer": args.optimizer,
        "muon_lr": args.muon_lr,
        "scheduler": args.scheduler,
        "stable_ratio": args.stable_ratio,
    }
    _train_overrides = {k: v for k, v in _TRAIN_CLI_MAP.items() if v is not None}
    if _train_overrides:
        _base = {f.name: getattr(train_config, f.name) for f in fields(train_config)}
        train_config = type(train_config)(**{**_base, **_train_overrides})

    if args.config:
        model_config = M01Config.from_yaml(args.config)
    else:
        model_config = M01Config()

    if args.vocab_size is not None:
        _base = {f.name: getattr(model_config, f.name) for f in fields(model_config)}
        model_config = type(model_config)(**{**_base, "vocab_size": args.vocab_size})

    model = TransformerLM(model_config)

    if args.device == "cpu":
        device = torch.device("cpu")
    elif args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()):
        device = torch.device("cuda")
    elif args.device == "dml":
        import torch_directml
        device = torch_directml.device()
    else:
        try:
            import torch_directml
            device = torch_directml.device()
        except Exception:
            device = torch.device("cpu")

    # Mover modelo al dispositivo inmediatamente tras resolver device y ANTES
    # de apply_fp8_linear, configure_optimizer y torch.compile
    model = model.to(device)

    # --- FP8 Training (RDNA4 native, no-op on unsupported devices) ---
    if args.fp8 and device.type == "cuda":
        model = apply_fp8_linear(model, verbose=True)
        print("[FP8] Float8Linear active — e4m3fnuz (AMD native format), dynamic scaling, BF16 accumulation.")
    elif args.fp8:
        print("[FP8] WARNING: FP8 requested but device is not CUDA/ROCm — running in BF16.")

    print(f"[M0.1 ENTERPRISE TRAINING ENGINE V2] Running on {device}")
    print(f"  Optimizer: {train_config.optimizer.upper()} (Muon LR: {train_config.muon_lr}, AdamW LR: {train_config.max_lr})")
    print(f"  Scheduler: {train_config.scheduler.upper()} (Warmup: {train_config.warmup_steps}, Max Steps: {train_config.max_steps})")
    print(f"  Precision: {'FP8 (e4m3fnuz) → BF16 accum' if args.fp8 and device.type == 'cuda' else 'BF16 (AMP)'}")


    # Dataset & Loaders
    full_dataset = build_training_dataset(train_config, corpus_dir=args.corpus_dir, load_to_ram=args.load_to_ram)
    total_samples = len(full_dataset)
    is_sliding_window = (
        isinstance(full_dataset, TinyShakespeareDataset)
        or getattr(full_dataset, "stride", getattr(full_dataset, "seq_len", 1)) < getattr(full_dataset, "seq_len", 1024)
    )
    # Split secuencial para ventanas deslizantes para evitar fuga de tokens contiguos entre train y val
    if is_sliding_window:
        train_size = int(0.90 * total_samples)
        val_size = total_samples - train_size
        train_ds = torch.utils.data.Subset(full_dataset, range(0, train_size))
        val_ds = torch.utils.data.Subset(full_dataset, range(train_size, total_samples))
    else:
        train_size = int(0.95 * total_samples)
        val_size = total_samples - train_size
        train_ds, val_ds = torch.utils.data.random_split(full_dataset, [train_size, val_size])

    num_workers = 0 if sys.platform == "win32" else 4
    persistent_workers = (num_workers > 0)
    prefetch_factor = 2 if num_workers > 0 else None

    train_loader = DataLoader(
        train_ds,
        batch_size=train_config.batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
        persistent_workers=persistent_workers,
        prefetch_factor=prefetch_factor,
        worker_init_fn=worker_init_fn,
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=train_config.batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
        worker_init_fn=worker_init_fn,
    )

    # Optimizador y Scheduler Empresarial
    optimizer = configure_optimizer(
        model=model,
        config=train_config,
        optimizer_type=train_config.optimizer,
        muon_lr=train_config.muon_lr,
    )

    scheduler = get_lr_scheduler(
        optimizer=optimizer,
        warmup_steps=train_config.warmup_steps,
        max_steps=train_config.max_steps,
        min_lr_ratio=train_config.min_lr_ratio,
        scheduler_type=train_config.scheduler,
        stable_ratio=train_config.stable_ratio,
    )

    experiment_mgr = ExperimentManager(base_dir="runs", run_name=args.run_name)

    engine = TrainingEngineV2(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        train_loader=train_loader,
        val_loader=val_loader,
        config=train_config,
        experiment_manager=experiment_mgr,
        gradient_accumulation_steps=args.grad_accum_steps if args.grad_accum_steps is not None else train_config.grad_accum_steps,
        max_norm=train_config.max_norm,
        device=device,
    )

    # Auto-save merged config
    run_dir = engine.experiment.run_dir
    import yaml as _yaml
    config_data = {
        "model": {f.name: getattr(model_config, f.name) for f in fields(model_config)},
        "training": {f.name: getattr(train_config, f.name) for f in fields(train_config)},
        "enterprise": {
            "optimizer": train_config.optimizer,
            "muon_lr": train_config.muon_lr,
            "scheduler": train_config.scheduler,
            "stable_ratio": train_config.stable_ratio,
        }
    }
    with open(os.path.join(run_dir, "config.yaml"), "w", encoding="utf-8") as f:
        _yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Reanudación de checkpoint antes de torch.compile para evitar prefijos _orig_mod.
    if args.resume:
        resume_path = None if args.resume == "__canonical__" else args.resume
        engine.resume(resume_path)

    # Compilación TorchInductor en modo default (seguro contra dynamic control flow de MoE)
    if hasattr(torch, "compile") and device.type == "cuda" and sys.platform != "win32":
        try:
            print("[INFO] Compilando modelo con torch.compile(mode='default')...")
            engine.model = torch.compile(engine.model, mode="default")
        except Exception as e:
            print(f"[WARNING] No se pudo aplicar torch.compile: {e}")

    t_start = time.time()
    summary = engine.fit(max_steps=train_config.max_steps)
    t_end = time.time()

    # Hardware & Speed Stats
    cpu_usage = psutil.cpu_percent() if psutil else 0.0
    ram_usage = psutil.virtual_memory().percent if psutil else 0.0
    vram_metrics = get_cuda_memory_metrics_mb()
    elapsed = t_end - t_start

    print("\n" + "=" * 60)
    print("           M0.1 — RUN COMPLETION REPORT")
    print("=" * 60)
    print(f"  Total steps:       {summary['final_step']}")
    print(f"  Total tokens seen: {summary['total_tokens']:,}")
    print(f"  Elapsed time:      {elapsed:.2f} seconds ({elapsed/60:.2f} mins)")
    print(f"  Final Loss:        {summary['final_loss']:.4f}")
    print(f"  Final LR:          {scheduler.get_last_lr()[0]:.2e}")
    print(f"  GPU VRAM allocated:      {vram_metrics['vram_alloc_mb']:.1f} MB")
    print(f"  GPU VRAM reserved:       {vram_metrics['vram_reserved_mb']:.1f} MB")
    print(f"  GPU VRAM peak reserved:  {vram_metrics['vram_reserved_peak_mb']:.1f} MB")
    print(f"  CPU Usage:         {cpu_usage:.1f}%")
    print(f"  RAM Usage:         {ram_usage:.1f}%")
    print(f"  Run Directory:     {engine.experiment.run_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
