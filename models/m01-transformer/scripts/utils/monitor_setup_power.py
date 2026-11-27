#!/usr/bin/env python3
"""Monitor de consumo eléctrico y telemetría de la torre completa calibrado con tarifas reales de Chile (Cauquenes, Región del Maule).

Tarifa oficial de referencia:
- Ubicación: Comuna de Cauquenes, Región del Maule, Chile.
- Distribuidora: CGE Distribución (Suministro BT1 Residencial aéreo convencional STxE-7-A).
- Componentes por kWh consumido (CNE / Decretos tarifarios vigentes con PEC e IVA 19%):
  * Cargo por energía base y compras de potencia: ~$172 CLP/kWh
  * Peajes de transporte y transmisión troncal Maule: ~$28 CLP/kWh
  * Servicio público y distribución comunal aérea: ~$23 CLP/kWh
  * IVA (19% sobre componentes afectos): ~$42 CLP/kWh
  * Costo real total consolidado en boleta Cauquenes: ~$265 CLP/kWh.

Hardware Target:
- GPU: AMD Radeon RX 9060 XT 16GB (ROCm 6.3 / WSL2).
- Perfil del usuario: Undervolt de -75mV en núcleo, Power Limit recortado a 130W (-30%).
- Plataforma base: CPU moderna, placa base, RAM DDR5, NVMe, refrigeración.
- Fuente de Poder: 80+ Gold (eficiencia dinámica 81% en idle a 89% bajo carga).
"""

import os
import sys
import time
import json
import argparse
import subprocess
import psutil
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Configuración por defecto Cauquenes / Maule
DEFAULT_CAUQUENES_CLP_KWH = 265.0  # $265 CLP por kWh real en boleta Cauquenes (CGE BT1 c/ IVA)

# Perfil físico de hardware
GPU_POWER_LIMIT_CAP = 130.0        # Límite estricto configurado en driver/BIOS
UNDERVOLT_OFFSET_WATTS = 12.0      # Reducción media de consumo lograda con -75mV


def query_amd_smi_sensor() -> tuple[float, float, float, bool]:
    """Consulta los sensores físicos de la GPU AMD vía amd-smi CLI en WSL2.

    Retorna: (potencia_watts, vram_usada_mb, actividad_gfx_pct, lectura_exitosa)
    """
    try:
        cmd = ["amd-smi", "metric", "-p", "-m", "-u", "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            gpu0 = data["gpu_data"][0]
            socket_power = float(gpu0["power"]["socket_power"]["value"])
            used_vram = float(gpu0["mem_usage"]["used_vram"]["value"])
            gfx_activity = float(gpu0["usage"]["gfx_activity"]["value"])
            # Aplicar cap por software como salvaguarda
            capped_power = min(GPU_POWER_LIMIT_CAP, socket_power)
            return capped_power, used_vram, gfx_activity, True
    except Exception:
        pass
    return 18.0, 0.0, 0.0, False


def detect_active_compute_process() -> tuple[bool, str]:
    """Detecta si hay procesos de entrenamiento, inferencia o cómputo pesado activos."""
    compute_keywords = [
        "train_sft", "train_align", "train.py", "pretrain",
        "eval_", "benchmark", "generate.py", "torchrun", "accelerate"
    ]
    try:
        for proc in psutil.process_iter(["name", "cmdline"]):
            cmd = " ".join(proc.info["cmdline"] or [])
            for kw in compute_keywords:
                if kw in cmd:
                    return True, proc.info["name"] or kw
    except Exception:
        pass
    return False, ""


def calculate_instant_power(
    cpu_percent: float,
    gpu_power_sensor: float,
    sensor_ok: bool,
    compute_active: bool,
    vram_mb: float,
) -> tuple[float, float, float, float]:
    """Calcula la potencia instantánea de la torre y la pared con curva de eficiencia de fuente.

    Retorna: (gpu_watts, platform_watts, total_wall_watts, psu_efficiency)
    """
    # 1. Potencia GPU
    if sensor_ok:
        gpu_watts = gpu_power_sensor
    else:
        # Fallback heurístico calibrado para RX 9060 XT (-75mV undervolt, 130W cap)
        if compute_active or vram_mb > 3000:
            raw_watts = 105.0 + min(17.0, (vram_mb / 6000.0) * 17.0)
            gpu_watts = min(GPU_POWER_LIMIT_CAP, raw_watts)
        else:
            gpu_watts = 18.0  # Reposo con undervolt

    # 2. Potencia Plataforma (CPU, placa madre, DDR5, almacenamiento, ventiladores)
    base_platform = 60.0
    cpu_dynamic = (cpu_percent / 100.0) * 50.0
    platform_watts = base_platform + cpu_dynamic

    # 3. Potencia DC total
    total_dc_watts = gpu_watts + platform_watts

    # 4. Curva de eficiencia dinámica para fuente 80+ Gold:
    # ~81% a baja carga (idle ~80W DC) y ~88-89% a carga media/alta (180W-250W DC)
    psu_efficiency = 0.81 + 0.08 * min(1.0, max(0.0, (total_dc_watts - 70.0) / 130.0))
    total_wall_watts = total_dc_watts / psu_efficiency

    return gpu_watts, platform_watts, total_wall_watts, psu_efficiency


def compute_energy_and_cost(
    energy_joules: float, cost_kwh_clp: float
) -> tuple[float, float]:
    """Convierte Joules acumulados a kWh y costo en CLP."""
    total_kwh = energy_joules / (3600.0 * 1000.0)
    cost_clp = total_kwh * cost_kwh_clp
    return total_kwh, cost_clp


def main():
    parser = argparse.ArgumentParser(
        description="Monitor de Consumo Eléctrico de la Torre Completa (Cauquenes / Maule / Chile)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Intervalo de muestreo en segundos (defecto: 2.0)",
    )
    parser.add_argument(
        "--cost-kwh-clp",
        type=float,
        default=DEFAULT_CAUQUENES_CLP_KWH,
        help=f"Costo por kWh en CLP (defecto: ${DEFAULT_CAUQUENES_CLP_KWH:.1f} CLP, CGE Cauquenes BT1)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Archivo opcional para registrar métricas en CSV con timestamps ISO",
    )
    args = parser.parse_args()

    # Identificación rápida de hardware sin cargar PyTorch
    sensor_w, vram_mb, gfx_pct, has_amd_smi = query_amd_smi_sensor()
    telemetry_mode = "Sensor Hardware (amd-smi)" if has_amd_smi else "Heurística Calibrada"

    print("=" * 86)
    print("⚡ MONITOR DE CONSUMO ELÉCTRICO DE LA TORRE COMPLETA (SETUP ENTERO)")
    print(f"🔹 GPU: AMD Radeon RX 9060 XT (Cap: {GPU_POWER_LIMIT_CAP}W, Undervolt: -75mV)")
    print(f"🔹 Modo de Telemetría: {telemetry_mode}")
    print(f"🇨🇱 Tarifa calibrada: Cauquenes, Región del Maule (CGE BT1 Residencial aéreo)")
    print(f"💰 Precio kWh: ${args.cost_kwh_clp:.1f} CLP")
    print("=" * 86)
    print(
        f"{'Tiempo':>8s} | {'CPU%':>5s} | {'VRAM(MB)':>8s} | {'GPU(W)':>7s} | {'PC(W)':>6s} | {'Pared(W)':>8s} | {'PSU%':>5s} | {'kWh Acum':>9s} | {'CLP ($)':>9s}"
    )
    print("-" * 86)

    csv_handle = None
    if args.log_file:
        log_path = Path(args.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        csv_handle = open(log_path, "w", encoding="utf-8")
        csv_handle.write(
            "iso_time,elapsed_sec,cpu_pct,vram_mb,gpu_w,platform_w,wall_w,psu_eff,total_kwh,cost_clp\n"
        )

    start_time = time.time()
    last_time = start_time
    total_energy_joules = 0.0

    # Potencia inicial para la integración trapezoidal
    _, _, prev_wall_w, _ = calculate_instant_power(
        cpu_percent=10.0,
        gpu_power_sensor=sensor_w,
        sensor_ok=has_amd_smi,
        compute_active=False,
        vram_mb=vram_mb,
    )

    try:
        while True:
            # 1. Muestreo bloqueante de CPU (espera interval segundos)
            cpu_pct = psutil.cpu_percent(interval=args.interval)

            # 2. Medir dt inmediatamente después del muestreo para eliminar el desfase
            now = time.time()
            dt = now - last_time
            last_time = now

            # 3. Telemetría de GPU y Procesos
            gpu_sensor_w, used_vram, gfx_act, sensor_ok = query_amd_smi_sensor()
            compute_active, proc_name = detect_active_compute_process()

            # 4. Potencia instantánea con curva dinámica de PSU
            gpu_w, sys_w, curr_wall_w, psu_eff = calculate_instant_power(
                cpu_percent=cpu_pct,
                gpu_power_sensor=gpu_sensor_w,
                sensor_ok=sensor_ok,
                compute_active=compute_active,
                vram_mb=used_vram,
            )

            # 5. Integración numérica trapezoidal: ΔE = ((P_prev + P_curr) / 2) * dt
            step_energy_joules = ((prev_wall_w + curr_wall_w) / 2.0) * dt
            total_energy_joules += step_energy_joules
            prev_wall_w = curr_wall_w

            # 6. Conversión a métricas energéticas y de costo
            total_kwh, cost_clp = compute_energy_and_cost(
                total_energy_joules, args.cost_kwh_clp
            )

            elapsed = int(now - start_time)
            mins, secs = divmod(elapsed, 60)
            time_str = f"{mins:02d}:{secs:02d}"

            print(
                f"{time_str:>8s} | {cpu_pct:5.1f} | {used_vram:8.1f} | {gpu_w:6.1f}W | {sys_w:5.1f}W | {curr_wall_w:7.1f}W | {psu_eff*100:4.1f}% | {total_kwh:8.5f} | ${cost_clp:8.2f}"
            )
            sys.stdout.flush()

            if csv_handle:
                iso_str = datetime.now().isoformat(timespec="seconds")
                csv_handle.write(
                    f"{iso_str},{elapsed},{cpu_pct:.1f},{used_vram:.1f},{gpu_w:.1f},{sys_w:.1f},{curr_wall_w:.1f},{psu_eff:.3f},{total_kwh:.6f},{cost_clp:.3f}\n"
                )
                csv_handle.flush()

    except KeyboardInterrupt:
        pass
    finally:
        elapsed = time.time() - start_time
        total_kwh, cost_clp = compute_energy_and_cost(
            total_energy_joules, args.cost_kwh_clp
        )
        avg_power = (total_energy_joules / elapsed) if elapsed > 0 else 0.0

        print("\n" + "=" * 86)
        print("📊 RESUMEN FINAL DE CONSUMO Y COSTO ELÉCTRICO (CAUQUENES, MAULE)")
        print(f"⏱️ Tiempo monitoreado: {elapsed:.1f} segundos ({elapsed/60:.2f} min)")
        print(f"⚡ Energía total consumida: {total_kwh:.6f} kWh ({total_energy_joules/1000:.2f} kJ)")
        print(f"🔌 Potencia promedio de la pared: {avg_power:.1f} Watts")
        print(f"🇨🇱 Costo eléctrico total (Cauquenes CGE BT1): ${cost_clp:,.2f} CLP")
        print("=" * 86)
        if csv_handle:
            csv_handle.close()


if __name__ == "__main__":
    main()
