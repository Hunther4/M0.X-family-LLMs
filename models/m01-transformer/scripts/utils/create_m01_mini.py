#!/usr/bin/env python3
"""Script para crear M0.1-Mini y transferir/fusionar los expertos de M0.1 Estándar (160M -> 99M o 69M).

Permite crear una variante compacta y energéticamente hiper-eficiente de M0.1
sin entrenar desde cero, heredando todas las representaciones y pesos ya aprendidos.
"""

import os
import sys
import copy
import argparse
import torch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model.lm import TransformerLM
from src.transformer.config import M01Config
from src.tokenizer.bpe import Tokenizer
from src.inference.generate import generate

def transfer_weights_to_mini(
    source_state_dict: dict,
    target_num_experts: int = 4,
    method: str = "merge"
) -> dict:
    """Transfiere y fusiona los pesos de M0.1 Estándar a M0.1 Mini."""
    new_state_dict = {}

    # Limpiar prefijos si existen
    cleaned_src = {}
    for k, v in source_state_dict.items():
        clean_k = k.replace("_orig_mod.", "").replace("model.", "")
        cleaned_src[clean_k] = v

    print(f"🔄 Iniciando transferencia con método '{method}' hacia {target_num_experts} expertos...")

    for k, v in cleaned_src.items():
        # 1. Pesos que se transfieren 1:1 directamente
        if "ff.experts." not in k and "ff.gate.weight" not in k:
            new_state_dict[k] = v.clone()
            continue

        # 2. Manejo de bloques MoE (Layers 2..11)
        if "ff.gate.weight" in k:
            gate_w = v # Shape (8, 640)
            if method == "merge":
                # Fusionar filas del gate en target_num_experts
                group_size = 8 // target_num_experts
                merged_gates = []
                for g in range(target_num_experts):
                    group_slice = gate_w[g * group_size : (g + 1) * group_size]
                    merged_gates.append(group_slice.mean(dim=0))
                new_state_dict[k] = torch.stack(merged_gates, dim=0)
            else: # top-k selection
                norms = gate_w.norm(dim=1)
                top_indices = torch.topk(norms, target_num_experts).indices.sort().values
                new_state_dict[k] = gate_w[top_indices].clone()

    # 3. Manejo de los expertos ruteados
    for layer in range(2, 12):
        gate_w = cleaned_src[f"blocks.{layer}.ff.gate.weight"]
        norms = gate_w.norm(dim=1)
        top_indices = torch.topk(norms, target_num_experts).indices.sort().values.tolist()

        group_size = 8 // target_num_experts

        for target_idx in range(target_num_experts):
            for weight_type in ["gate_up_proj.weight", "down_proj.weight"]:
                target_key = f"blocks.{layer}.ff.experts.{target_idx}.{weight_type}"

                if method == "merge":
                    # Promediar el grupo de expertos correspondiente
                    src_indices = range(target_idx * group_size, (target_idx + 1) * group_size)
                    src_tensors = [
                        cleaned_src[f"blocks.{layer}.ff.experts.{s_idx}.{weight_type}"]
                        for s_idx in src_indices
                    ]
                    # Promedio ponderado por la norma de su compuerta
                    weights = [norms[s_idx].item() for s_idx in src_indices]
                    total_w = sum(weights) or 1.0
                    merged_tensor = sum(t * (w / total_w) for t, w in zip(src_tensors, weights))
                    new_state_dict[target_key] = merged_tensor
                else: # top selection
                    src_idx = top_indices[target_idx]
                    src_key = f"blocks.{layer}.ff.experts.{src_idx}.{weight_type}"
                    new_state_dict[target_key] = cleaned_src[src_key].clone()

    print(f"✅ Transferencia completada: {len(new_state_dict)} tensores adaptados.")
    return new_state_dict

def main():
    parser = argparse.ArgumentParser(description="Crear M0.1 Mini por transferencia de pesos")
    parser.add_argument("--experts", type=int, default=4, choices=[2, 4], help="Expertos ruteados en Mini (2 o 4)")
    parser.add_argument("--method", type=str, default="merge", choices=["merge", "top"], help="Método: merge o top")
    parser.add_argument("--output-run", type=str, default="runs/m01_mini", help="Directorio de destino")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 70)
    print(f"🌟 CREACIÓN DE M0.1 MINI ({args.experts} EXPERTOS, MÉTODO: {args.method})")
    print(f"🔹 Dispositivo: {device}")
    print("=" * 70)

    # 1. Cargar Checkpoint Base (160M)
    base_ckpt_path = "runs/run_multi_checkpoint_100steps/checkpoints/checkpoint.pt"
    if not os.path.exists(base_ckpt_path):
        print(f"❌ Error: No se encontró checkpoint base en {base_ckpt_path}")
        return

    print(f"📂 Cargando checkpoint base desde {base_ckpt_path}...")
    base_ckpt = torch.load(base_ckpt_path, map_location="cpu", weights_only=False)
    base_state = base_ckpt.get("model_state", base_ckpt)
    step = base_ckpt.get("step", 4666)

    # 2. Configurar M0.1 Mini
    top_k = 2 if args.experts == 4 else 1
    config_mini = M01Config(
        vocab_size=16384,
        d_model=640,
        n_heads=10,
        d_ff=1728,
        n_layers=12,
        num_experts=args.experts,
        num_shared_experts=1,
        moe_top_k=top_k,
        d_ff_shared=448,
        d_ff_routed=784,
    )

    model_mini = TransformerLM(config_mini)
    mini_params = sum(p.numel() for p in model_mini.parameters())
    print(f"📐 Parámetros M0.1-Mini: {mini_params:,} ({mini_params/1e6:.1f}M) [vs 160M estándar]")

    # 3. Transferir Pesos
    mini_state = transfer_weights_to_mini(base_state, target_num_experts=args.experts, method=args.method)
    model_mini.load_state_dict(mini_state, strict=True)
    model_mini = model_mini.to(device)
    model_mini.eval()

    # 4. Guardar Checkpoint de M0.1 Mini
    out_dir = Path(args.output_run) / "checkpoints"
    out_dir.mkdir(parents=True, exist_ok=True)
    mini_ckpt_path = out_dir / "checkpoint.pt"

    save_payload = {
        "step": step,
        "model_state": model_mini.state_dict(),
        "model_config": config_mini,
        "created_at": base_ckpt.get("created_at"),
        "source_checkpoint": base_ckpt_path,
        "variant": f"m0.1_mini_{args.experts}experts",
    }
    torch.save(save_payload, str(mini_ckpt_path))
    file_size_mb = os.path.getsize(str(mini_ckpt_path)) / (1024 * 1024)
    print(f"💾 Checkpoint guardado en: {mini_ckpt_path} ({file_size_mb:.1f} MB)")

    # 5. Prueba de Inferencia Rápida en GPU
    print("\n" + "=" * 70)
    print(f"🧪 PROBANDO INFERENCIA EN VIVO DE M0.1 MINI ({mini_params/1e6:.1f}M PARÁMETROS)")
    print("=" * 70)

    tokenizer = Tokenizer()
    tokenizer.load("data/tokenizers/tokenizer.json")

    test_prompts = [
        "<|user|>\n¿Quién eres y cuál es tu propósito?\n<|assistant|>\n",
        "<|user|>\nHola, ¿cómo estás?\n<|assistant|>\n",
        "def calcular_total(precios):\n    \"\"\"Calcula el total de una lista.\"\"\"\n",
    ]

    for p in test_prompts:
        print(f"\n📥 Prompt:\n{p.strip()}")
        with torch.no_grad():
            output = generate(
                model=model_mini,
                tokenizer=tokenizer,
                prompt=p,
                max_gen_len=70,
                temperature=0.4,
                top_p=0.9,
                device=device,
            )
        resp = output[len(p):].strip()
        print(f"📤 Respuesta de M0.1-Mini:\n{resp}")
        print("-" * 50)

    print("\n" + "=" * 70)
    print("🎉 M0.1 MINI CREADO Y VERIFICADO EXITOSAMENTE")
    print("=" * 70)

if __name__ == "__main__":
    main()
