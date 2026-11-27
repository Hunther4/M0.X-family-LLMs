import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import torch
import time
import json
from src.transformer.attention_backend import AttentionDispatcher

def benchmark_sdpa():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Benchmarking SDPA backends on device: {device}")
    
    backends = ["auto", "math", "efficient", "flash"]
    batch_seq = 2048
    d_model = 640
    n_heads = 10
    head_dim = 64
    
    q = torch.randn(1, batch_seq, n_heads, head_dim, device=device, dtype=torch.bfloat16)
    k = torch.randn(1, batch_seq, n_heads, head_dim, device=device, dtype=torch.bfloat16)
    v = torch.randn(1, batch_seq, n_heads, head_dim, device=device, dtype=torch.bfloat16)
    
    results = {}
    for backend in backends:
        try:
            dispatcher = AttentionDispatcher(preferred_backend=backend)
            
            # Warmup
            for _ in range(10):
                _ = dispatcher.dispatch(q, k, v, is_causal=True)
            torch.cuda.synchronize()
            
            start = time.perf_counter()
            for _ in range(50):
                _ = dispatcher.dispatch(q, k, v, is_causal=True)
            torch.cuda.synchronize()
            end = time.perf_counter()
            
            ms = (end - start) * 1000.0 / 50
            results[backend] = {"latency_ms": ms, "status": "success"}
            print(f"SDPA backend [{backend}]: {ms:.2f} ms")
        except Exception as e:
            results[backend] = {"status": "failed", "error": str(e)}
            print(f"SDPA backend [{backend}]: FAILED ({e})")
            
    os.makedirs("docs/benchmark_results", exist_ok=True)
    with open("docs/benchmark_results/sdpa_backend_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    benchmark_sdpa()
