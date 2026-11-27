"""Script Refactorizado y Optimizado para SFT (Supervised Fine-Tuning) de M0.1.

Utiliza:
- TrainingEngineV2 (FSM recovery, telemetría MoE, checkpointing asíncrono)
- Enterprise Hybrid Muon + AdamW Optimizer
- WSD (Warmup-Stable-Decay) o Cosine LR Scheduler
- GPU AMD ROCm / RDNA 4 (gfx1200) nativa con AOTriton kernels
- Tokenizer estándar de 16k (`data/tokenizers/tokenizer.json`)
- Corpus JSONL SFT real (`data/corpus_sft/instrucciones_sft_conversaciones_1m_tokens.jsonl`)

Uso:
  python -m scripts.training.train_sft --optimizer hybrid_muon --scheduler wsd --max-steps 200
"""

import argparse
import os
import sys
import shutil

# WSL2 ROCm compatibility: expandable_segments is not supported by the WSL2 Direct3D/KFD layer and causes hipErrorInvalidValue
if "PYTORCH_HIP_ALLOC_CONF" in os.environ and "expandable_segments" in os.environ["PYTORCH_HIP_ALLOC_CONF"]:
    _conf = os.environ["PYTORCH_HIP_ALLOC_CONF"].replace("expandable_segments:True", "").strip(",")
    if _conf:
        os.environ["PYTORCH_HIP_ALLOC_CONF"] = _conf
    else:
        del os.environ["PYTORCH_HIP_ALLOC_CONF"]

# WSL2 ROCm memory allocator tuning: keep pool compact and prevent shared RAM spillover
if "PYTORCH_CUDA_ALLOC_CONF" not in os.environ or not os.environ["PYTORCH_CUDA_ALLOC_CONF"]:
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "garbage_collection_threshold:0.5,max_split_size_mb:64"
if "PYTORCH_HIP_ALLOC_CONF" not in os.environ or not os.environ["PYTORCH_HIP_ALLOC_CONF"]:
    os.environ["PYTORCH_HIP_ALLOC_CONF"] = "garbage_collection_threshold:0.5,max_split_size_mb:64"

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
from src.engine_v2.bus import EngineEvent


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="M0.1 SFT Training Pipeline con Engine V2 y Muon+WSD.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Ruta al checkpoint inicial opcional (si no se pasa o no existe, inicia desde cero)",
    )
    default_corpus = (
        "data/corpus_sft/instrucciones_sft_conversaciones_1m_tokens.jsonl"
        if os.path.exists("data/corpus_sft/instrucciones_sft_conversaciones_1m_tokens.jsonl")
        else "data/corpus_sft/corpus_sft_1m.jsonl"
    )
    parser.add_argument(
        "--sft-corpus",
        type=str,
        default=default_corpus,
        help="Ruta al archivo JSONL del corpus SFT",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Batch size (defecto: 4)",
    )
    parser.add_argument(
        "--seq-len",
        type=int,
        default=1024,
        help="Longitud de secuencia (defecto: 1024)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=200,
        help="Pasos de entrenamiento (defecto: 200)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1.5e-4,
        help="Learning rate para AdamW (defecto: 1.5e-4)",
    )
    parser.add_argument(
        "--optimizer",
        type=str,
        choices=["hybrid_muon", "adamw"],
        default="hybrid_muon",
        help="Optimizador: 'hybrid_muon' o 'adamw' (defecto: hybrid_muon)",
    )
    parser.add_argument(
        "--muon-lr",
        type=float,
        default=0.02,
        help="Learning rate para Muon (defecto: 0.02)",
    )
    parser.add_argument(
        "--scheduler",
        type=str,
        choices=["wsd", "cosine"],
        default="wsd",
        help="Scheduler de LR: 'wsd' o 'cosine' (defecto: wsd)",
    )
    parser.add_argument(
        "--stable-ratio",
        type=float,
        default=0.8,
        help="Ratio de fase estable para scheduler WSD (defecto: 0.8)",
    )
    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=20,
        help="Pasos de warmup (defecto: 20)",
    )
    parser.add_argument(
        "--save-interval",
        type=int,
        default=50,
        help="Intervalo de pasos para guardar checkpoint canónico (defecto: 50)",
    )
    parser.add_argument(
        "--grad-accum-steps",
        type=int,
        default=2,
        help="Pasos de acumulación de gradiente (defecto: 2, batch efectivo = 8)",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=1_000_000,
        help="Líneas máximas a leer del dataset (defecto: 1000000)",
    )
    parser.add_argument(
        "--num-experts",
        type=int,
        default=None,
        help="Número de expertos ruteados (defecto: auto-detectar de checkpoint u 8)",
    )
    parser.add_argument(
        "--moe-top-k",
        type=int,
        default=None,
        help="Top-K expertos activos (defecto: auto-detectar de checkpoint o 2)",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default="run_muon_wsd_200steps",
        help="Nombre de la corrida y directorio en runs/",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args(sys.argv[1:])

    # Verificación obligatoria de ejecución en GPU AMD ROCm (sin fallback silencioso a CPU)
    assert torch.cuda.is_available(), (
        "FATAL: CUDA/ROCm no disponible. Se requiere GPU AMD ROCm (gfx1200) para ejecutar este entrenamiento."
    )
    device = torch.device("cuda")
    gpu_name = torch.cuda.get_device_name(device)
    print(f"[M0.1 SFT ENGINE V2] GPU confirmada y activa: {gpu_name} ({device})")

    # Set VRAM headroom cap to 85% (~13.4 GB) to prevent Windows shared memory spillover while allowing forward peaks
    torch.cuda.set_per_process_memory_fraction(0.85, device=0)

    # 1. Cargar Tokenizer estándar de 16k
    tokenizer_path = os.path.join("data", "tokenizers", "tokenizer.json")
    tokenizer = Tokenizer()
    if os.path.exists(tokenizer_path):
        print(f"[M0.1 SFT] Cargando Tokenizer de 16k desde {tokenizer_path}...")
        tokenizer.load(tokenizer_path)
    else:
        print("[M0.1 SFT] Usando Tokenizer base...")

    def resolve_path(p: str | None) -> str | None:
        if not p or str(p).strip().lower() == "none":
            return None
        pt = Path(p)
        if pt.is_absolute() and pt.exists():
            return str(pt)
        if (REPO_ROOT / pt).exists():
            return str(REPO_ROOT / pt)
        if pt.exists():
            return str(pt.resolve())
        return None

    # Detectar checkpoint objetivo antes de instanciar modelo
    canonical_ckpt = resolve_path(os.path.join("runs", args.run_name, "checkpoints", "checkpoint.pt"))
    target_ckpt = resolve_path(args.checkpoint) or canonical_ckpt

    num_experts = args.num_experts if args.num_experts is not None else 8
    moe_top_k = args.moe_top_k if args.moe_top_k is not None else 2

    d_ff_shared = 448 if num_experts == 2 else 448
    d_ff_routed = 784 if num_experts == 2 else 1728

    if target_ckpt:
        try:
            ckpt_meta = torch.load(target_ckpt, map_location="cpu", weights_only=False)
            saved_cfg = ckpt_meta.get("model_config")
            if saved_cfg is not None:
                if isinstance(saved_cfg, dict):
                    num_experts = saved_cfg.get("num_experts", num_experts)
                    moe_top_k = saved_cfg.get("moe_top_k", moe_top_k)
                    d_ff_shared = saved_cfg.get("d_ff_shared", d_ff_shared)
                    d_ff_routed = saved_cfg.get("d_ff_routed", d_ff_routed)
                elif hasattr(saved_cfg, "num_experts"):
                    num_experts = saved_cfg.num_experts
                    moe_top_k = saved_cfg.moe_top_k
                    d_ff_shared = getattr(saved_cfg, "d_ff_shared", d_ff_shared)
                    d_ff_routed = getattr(saved_cfg, "d_ff_routed", d_ff_routed)
                print(f"[M0.1 SFT] Configuración MoE auto-detectada de {target_ckpt}: {num_experts} expertos, top-{moe_top_k} (shared={d_ff_shared}, routed={d_ff_routed})")
        except Exception as e:
            print(f"[M0.1 SFT] Advertencia al leer config de checkpoint: {e}")

    # 2. Configurar Modelo M0.1 con vocabulario 16k y mover inmediatamente a GPU
    model_config = M01Config(
        vocab_size=16384,
        num_experts=num_experts,
        moe_top_k=moe_top_k,
        d_ff_shared=d_ff_shared,
        d_ff_routed=d_ff_routed,
    )
    model = TransformerLM(model_config).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"[M0.1 SFT] Modelo M0.1 inicializado en GPU ({total_params:,} parámetros, {num_experts} expertos).")

    # 3. Cargar Dataset JSONL de SFT
    sft_corpus_path = resolve_path(args.sft_corpus) or args.sft_corpus
    if not os.path.exists(sft_corpus_path):
        raise FileNotFoundError(f"Corpus SFT no encontrado en {args.sft_corpus}.")

    print(f"[M0.1 SFT] Cargando dataset JSONL SFT desde {sft_corpus_path}...")
    sft_ds = JsonlDataset(
        tokenizer=tokenizer,
        paths=[sft_corpus_path],
        seq_len=args.seq_len,
        max_lines_per_shard=args.max_lines,
    )

    # WSL2 ROCm: num_workers=0 prevents fork deadlocks and D3D12 driver TDR crashes
    num_workers = 0
    persistent_workers = False
    prefetch_factor = None

    train_loader = DataLoader(
        sft_ds,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
        persistent_workers=persistent_workers,
        prefetch_factor=prefetch_factor,
        worker_init_fn=worker_init_fn,
    )

    train_config = TrainingConfig(
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        max_lr=args.lr,
        min_lr_ratio=0.1,
        warmup_steps=args.warmup_steps,
        max_steps=args.max_steps,
        weight_decay=0.01,
        max_norm=1.0,
        log_interval=10,
        save_interval=args.save_interval,
        val_interval=500,
        optimizer=args.optimizer,
        muon_lr=args.muon_lr,
        scheduler=args.scheduler,
        stable_ratio=args.stable_ratio,
    )

    optimizer = configure_optimizer(
        model=model,
        config=train_config,
        optimizer_type=args.optimizer,
        muon_lr=args.muon_lr,
    )
    scheduler = get_lr_scheduler(
        optimizer=optimizer,
        warmup_steps=train_config.warmup_steps,
        max_steps=train_config.max_steps,
        min_lr_ratio=train_config.min_lr_ratio,
        scheduler_type=args.scheduler,
        stable_ratio=args.stable_ratio,
    )

    experiment_mgr = ExperimentManager(base_dir=str(REPO_ROOT / "runs"), run_name=args.run_name)

    engine = TrainingEngineV2(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        train_loader=train_loader,
        val_loader=None,
        config=train_config,
        experiment_manager=experiment_mgr,
        gradient_accumulation_steps=args.grad_accum_steps,
        max_norm=train_config.max_norm,
        device=device,
    )

    # 4. Reanudar desde checkpoint detectado
    if target_ckpt:
        print(f"[M0.1 SFT] Reanudando entrenamiento desde checkpoint: {target_ckpt}")
        engine.resume(target_ckpt)
    else:
        print("[M0.1 SFT] Checkpoint no especificado o inexistente. Iniciando entrenamiento desde cero.")

    start_step = engine.current_step
    target_max_steps = args.max_steps
    if target_max_steps <= start_step:
        target_max_steps = start_step + args.max_steps

    checkpoint_dir = REPO_ROOT / "runs" / args.run_name / "checkpoints"

    def on_checkpoint_saved(file: str = "checkpoint.pt", **kwargs):
        curr_step = engine.current_step
        steps_trained = curr_step - start_step
        tok_step = args.batch_size * args.grad_accum_steps * args.seq_len
        tokens_added = steps_trained * tok_step
        canon_file = checkpoint_dir / "checkpoint.pt"
        if canon_file.exists():
            milestone_m = round(tokens_added / 1_000_000)
            if milestone_m > 0 and milestone_m % 5 == 0:
                milestone_path = checkpoint_dir / f"checkpoint_{milestone_m}M.pt"
                shutil.copy2(canon_file, milestone_path)
                print(f"\n[MILESTONE] 💾 Checkpoint de hito {milestone_m}M guardado en {milestone_path} (Paso {curr_step}, +{tokens_added:,} tokens)\n")

    engine.bus.subscribe(EngineEvent.CHECKPOINT_COMPLETE, on_checkpoint_saved)

    print(
        f"[M0.1 SFT] ¡Iniciando entrenamiento desde paso {start_step} hasta {target_max_steps} (+{target_max_steps - start_step} pasos)! "
        f"(Opt: {args.optimizer}, Sched: {args.scheduler}, Batch: {args.batch_size}, Accum: {args.grad_accum_steps}, Seq: {args.seq_len})"
    )
    summary = engine.fit(max_steps=target_max_steps)
    print(f"[M0.1 SFT] ¡Entrenamiento SFT finalizado! Resumen: {summary}")
    print(f"[M0.1 SFT] Checkpoints guardados en runs/{args.run_name}/checkpoints/")


if __name__ == "__main__":
    main()
