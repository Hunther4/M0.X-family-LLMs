"""Automated 1-Epoch 100M Token Pretraining Runner for M0.1.

Executes exactly 1 complete single pass over the 100,000,000 token corpus
without duplicate repeats, using the SOTA Enterprise Hybrid Muon + AdamW optimizer
and WSD (Warmup-Stable-Decay) learning rate schedule.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def wait_for_corpus(corpus_dir: str, target_tokens: int = 100_000_000, check_interval: int = 5) -> None:
    manifest_path = Path(corpus_dir) / "manifest.json"
    print(f"[PRETRAIN RUNNER] Waiting for corpus in {corpus_dir} to reach {target_tokens:,} tokens...")
    while True:
        if manifest_path.is_file():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                total_tokens = manifest.get("total_tokens", 0)
                shards_count = manifest.get("shards_count", 0)
                if total_tokens >= target_tokens:
                    print(f"[READY] Corpus generation complete! Total tokens: {total_tokens:,} in {shards_count} shards.")
                    break
                else:
                    print(f"  [Progress] Current tokens: {total_tokens:,} / {target_tokens:,} ({shards_count} shards)...")
            except Exception:
                pass
        time.sleep(check_interval)


def main():
    parser = argparse.ArgumentParser(description="Run 1-Epoch 100M Token Pretraining for M0.1")
    parser.add_argument("--corpus-dir", type=str, default=r"d:\Estuding\LLM_DATASETS\TOKENIZED\corpus_tier1_100m")
    parser.add_argument("--target-tokens", type=int, default=100_000_000)
    parser.add_argument("--seq-len", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--grad-accum-steps", type=int, default=4)
    parser.add_argument("--run-name", type=str, default="run_m01_tier1_100m_1epoch")
    args = parser.parse_args()

    # 1. Wait for sharder to finish writing the 100M tokens
    wait_for_corpus(args.corpus_dir, target_tokens=args.target_tokens)

    # 2. Compute exact steps for 1 single pass over the entire corpus
    tokens_per_step = args.batch_size * args.grad_accum_steps * args.seq_len  # e.g. 8 * 4 * 1024 = 32,768 tokens/step
    exact_steps = int(args.target_tokens / tokens_per_step)

    print("\n" + "=" * 65)
    print("       M0.1 — 1-EPOCH COMPLETE 100M TOKENS PRETRAINING")
    print("=" * 65)
    print(f"  Total Corpus Tokens:      {args.target_tokens:,}")
    print(f"  Sequence Length:          {args.seq_len}")
    print(f"  Micro-Batch Size:         {args.batch_size}")
    print(f"  Gradient Accumulation:    {args.grad_accum_steps}")
    print(f"  Global Batch Size:        {args.batch_size * args.grad_accum_steps} sequences ({tokens_per_step:,} tokens/step)")
    print(f"  Exact Total Steps:        {exact_steps:,} steps (1 single pass / 1 epoch)")
    print(f"  Optimizer:                Hybrid Muon (LR=0.02) + AdamW (LR=0.0003)")
    print(f"  Scheduler:                WSD (Warmup=200, Stable=80%, Cosine Decay=20%)")
    print("=" * 65 + "\n")

    # 3. Launch training
    cmd = [
        sys.executable,
        "-m", "src.training.train",
        "--config", "configs/base.yaml",
        "--corpus-dir", args.corpus_dir,
        "--run-name", args.run_name,
        "--optimizer", "hybrid_muon",
        "--muon-lr", "0.02",
        "--max-lr", "0.0003",
        "--scheduler", "wsd",
        "--stable-ratio", "0.8",
        "--warmup-steps", "200",
        "--max-steps", str(exact_steps),
        "--batch-size", str(args.batch_size),
        "--seq-len", str(args.seq_len),
        "--grad-accum-steps", str(args.grad_accum_steps),
        "--log-interval", "10",
        "--save-interval", "250",
    ]
    import subprocess
    subprocess.run(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    main()
