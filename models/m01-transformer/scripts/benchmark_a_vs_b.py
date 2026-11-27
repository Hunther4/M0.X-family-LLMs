"""Benchmark Config A (8 Experts) vs Config B (4 Experts) on RX 9060 XT in WSL2.

Runs 100 training steps each with identical seed, measuring:
- Tokens/sec throughput
- Step latency (ms/step)
- Peak VRAM (MB)
- Loss trajectory and final loss at step 100
"""

import os
import sys
import time

os.environ["HSA_ENABLE_DXG_DETECTION"] = "1"
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "12.0.0"
os.environ["TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL"] = "1"

sys.path.insert(0, "/mnt/d/Estuding/models/m01-transformer")

import torch
import torch.nn.functional as F
from src.transformer.config import M01Config
from src.model.lm import TransformerLM

def run_experiment(name: str, num_experts: int, steps: int = 100, batch_size: int = 4, seq_len: int = 512):
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    cfg = M01Config(
        vocab_size=16384,
        context_length=seq_len,
        d_model=640,
        n_heads=10,
        d_ff=1728,
        n_layers=12,
        num_dense_layers=2,
        num_experts=num_experts,
        num_shared_experts=1,
        moe_top_k=2,
        d_ff_shared=448,
        d_ff_routed=784,
        use_mla=True,
        mla_kv_c_dim=128,
        mla_rope_dim=16,
        partial_rotary_factor=0.25,
        swiglu_limit=10.0,
        scoring_func="sqrtsoftplus",
        kv_sharing_interval=1,
    )

    model = TransformerLM(cfg).to(device="cuda", dtype=torch.bfloat16)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.1)

    total_params = sum(p.numel() for p in model.parameters())

    # Pre-generate synthetic token batches with fixed seed
    torch.manual_seed(1337)
    batches = [
        torch.randint(0, cfg.vocab_size, (batch_size, seq_len + 1), device="cuda")
        for _ in range(steps)
    ]

    # Warmup step (JIT / kernel compilation)
    print(f"[{name}] Warming up kernels on {torch.cuda.get_device_name(0)}...", flush=True)
    warmup_x = batches[0][:, :-1]
    warmup_y = batches[0][:, 1:]
    out = model(warmup_x)
    loss = F.cross_entropy(out.reshape(-1, cfg.vocab_size), warmup_y.reshape(-1))
    loss.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    torch.cuda.synchronize()

    torch.cuda.reset_peak_memory_stats()
    print(f"[{name}] Starting 100 training steps (B={batch_size}, S={seq_len})...", flush=True)
    t_start = time.perf_counter()
    losses = []

    for step in range(steps):
        x = batches[step][:, :-1]
        y = batches[step][:, 1:]

        optimizer.zero_grad(set_to_none=True)
        logits = model(x)
        main_loss = F.cross_entropy(logits.reshape(-1, cfg.vocab_size), y.reshape(-1))
        aux_loss = model.get_aux_loss()
        total_loss = main_loss + aux_loss

        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        model.set_moe_step(step)

        losses.append(total_loss.item())
        if (step + 1) % 25 == 0 or step == steps - 1:
            print(f"  Step {step+1:3d}/{steps} | Loss: {total_loss.item():.4f} (Main: {main_loss.item():.4f}, Aux: {aux_loss.item():.4f})", flush=True)

    torch.cuda.synchronize()
    total_time = time.perf_counter() - t_start
    total_tokens = steps * batch_size * seq_len
    tokens_per_sec = total_tokens / total_time
    ms_per_step = (total_time / steps) * 1000
    peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

    return {
        "name": name,
        "num_experts": num_experts,
        "total_params": total_params,
        "total_time": total_time,
        "tokens_per_sec": tokens_per_sec,
        "ms_per_step": ms_per_step,
        "peak_vram_mb": peak_vram_mb,
        "final_loss": losses[-1],
        "initial_loss": losses[0],
    }

if __name__ == "__main__":
    print("=" * 60)
    print("BENCHMARK M0.1: CONFIG A (8 EXPERTOS) vs CONFIG B (4 EXPERTOS)")
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print("=" * 60)

    res_a = run_experiment("Config A (8 Expertos)", num_experts=8, steps=100)
    res_b = run_experiment("Config B (4 Expertos)", num_experts=4, steps=100)

    print("\n" + "=" * 60)
    print("RESULTADOS COMPARATIVOS EMPÍRICOS (100 STEPS):")
    print("=" * 60)
    print(f"{'Métrica':<25} | {'Config A (8 Exp)':<18} | {'Config B (4 Exp)':<18} | {'Diferencia':<12}")
    print("-" * 78)
    print(f"{'Parámetros Totales':<25} | {res_a['total_params']:>15,} | {res_b['total_params']:>15,} | -{(res_a['total_params']-res_b['total_params'])/1e6:.1f}M")
    print(f"{'Tokens / Segundo':<25} | {res_a['tokens_per_sec']:>15.1f} | {res_b['tokens_per_sec']:>15.1f} | {((res_b['tokens_per_sec']/res_a['tokens_per_sec'])-1)*100:+.2f}%")
    print(f"{'Latencia (ms / step)':<25} | {res_a['ms_per_step']:>15.1f} | {res_b['ms_per_step']:>15.1f} | {res_b['ms_per_step']-res_a['ms_per_step']:+.1f} ms")
    print(f"{'VRAM Pico (MB)':<25} | {res_a['peak_vram_mb']:>15.1f} | {res_b['peak_vram_mb']:>15.1f} | {res_b['peak_vram_mb']-res_a['peak_vram_mb']:+.1f} MB")
    print(f"{'Pérdida Inicial (Step 1)':<25} | {res_a['initial_loss']:>15.4f} | {res_b['initial_loss']:>15.4f} | {res_b['initial_loss']-res_a['initial_loss']:+.4f}")
    print(f"{'Pérdida Final (Step 100)':<25} | {res_a['final_loss']:>15.4f} | {res_b['final_loss']:>15.4f} | {res_b['final_loss']-res_a['final_loss']:+.4f}")
    print("=" * 78)
