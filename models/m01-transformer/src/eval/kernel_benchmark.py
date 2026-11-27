import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import torch
import torch.nn as nn
import torch.nn.functional as F
import time
import json
from src.transformer.fused_ffn import fused_swiglu

class BaselineFFN(nn.Module):
    def __init__(self, d_model=640, d_ff=1728):
        super().__init__()
        self.gate_proj = nn.Linear(d_model, d_ff, bias=False)
        self.up_proj = nn.Linear(d_model, d_ff, bias=False)
        self.down_proj = nn.Linear(d_ff, d_model, bias=False)

    def forward(self, x):
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))

class FusedFFN(nn.Module):
    def __init__(self, d_model=640, d_ff=1728):
        super().__init__()
        self.gate_proj = nn.Linear(d_model, d_ff, bias=False)
        self.up_proj = nn.Linear(d_model, d_ff, bias=False)
        self.down_proj = nn.Linear(d_ff, d_model, bias=False)

    def forward(self, x):
        gate = self.gate_proj(x)
        up = self.up_proj(x)
        intermediate = fused_swiglu(gate, up)
        return self.down_proj(intermediate)

def benchmark_fn(fn, *args, warmup=10, rep=50):
    for _ in range(warmup):
        fn(*args)
    torch.cuda.synchronize()
    
    start = time.perf_counter()
    for _ in range(rep):
        fn(*args)
    torch.cuda.synchronize()
    end = time.perf_counter()
    
    return (end - start) * 1000.0 / rep

def run_comparison():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Comparing Baseline FFN vs Fused FFN on device: {device}")
    
    shapes = [
        (512, 640, 1728),
        (2048, 640, 1728),
        (8192, 640, 1728),
    ]
    
    results = []
    for batch_seq, d_model, d_ff in shapes:
        x_base = torch.randn(batch_seq, d_model, device=device, dtype=torch.bfloat16, requires_grad=True)
        x_fused = x_base.clone().detach().requires_grad_(True)
        
        base_model = BaselineFFN(d_model, d_ff).to(device).to(torch.bfloat16)
        fused_model = FusedFFN(d_model, d_ff).to(device).to(torch.bfloat16)
        
        fused_model.gate_proj.weight.data.copy_(base_model.gate_proj.weight.data)
        fused_model.up_proj.weight.data.copy_(base_model.up_proj.weight.data)
        fused_model.down_proj.weight.data.copy_(base_model.down_proj.weight.data)
        
        def run_base():
            base_model.zero_grad()
            out = base_model(x_base)
            loss = out.sum()
            loss.backward()
            
        def run_fused():
            fused_model.zero_grad()
            out = fused_model(x_fused)
            loss = out.sum()
            loss.backward()
            
        ms_base = benchmark_fn(run_base)
        ms_fused = benchmark_fn(run_fused)
        
        speedup = (ms_base - ms_fused) / ms_base * 100.0
        
        print(f"Tokens={batch_seq} | Baseline: {ms_base:.2f} ms | Fused: {ms_fused:.2f} ms | Diff: {speedup:+.2f}%")
        results.append({
            "tokens": batch_seq,
            "baseline_ms": ms_base,
            "fused_ms": ms_fused,
            "improvement_pct": speedup
        })
        
    os.makedirs("docs/benchmark_results", exist_ok=True)
    with open("docs/benchmark_results/fused_ffn_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_comparison()
