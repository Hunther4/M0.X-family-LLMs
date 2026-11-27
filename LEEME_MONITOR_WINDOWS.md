# ⚡ Monitor Nativo de Energía y Telemetría Eléctrica para Windows

**Binario:** `power_monitor.exe` (Compilado en Go, nativo PE32+ para x86-64 Windows)  
**Código fuente:** `models/m01-transformer/scripts/utils/power_monitor_windows.go`

---

## 🎯 Características Principales

1. **100% Nativo de Windows (Sin dependencias Linux):**
   - Sin llamadas ni lecturas a rutas como `/proc` o `/sys`.
   - Medición precisa de uso de CPU usando llamadas a la API de Windows `kernel32.dll` (`GetSystemTimes`) mediante `syscall.NewLazyDLL` y `syscall.Filetime`.
   - Detección de procesos de cómputo en segundo plano mediante `CreateToolhelp32Snapshot`.

2. **Integración con LibreHardwareMonitor (LHM):**
   - Prioriza la lectura directa de telemetría de hardware conectándose al Web Server de LibreHardwareMonitor en `http://localhost:8085/data.json` (o `http://127.0.0.1:8085/data.json`).
   - Extrae automáticamente:
     - **GPU Package / Total Power** (Watts reales de la GPU).
     - **CPU Package Power** (Watts reales del paquete CPU).
     - **GPU Activity / Carga** (%).

3. **Fallback Heurístico Calibrado (Si LHM no está activo):**
   - **GPU Cap:** 130.0W (calibrado para AMD Radeon RX 9060 XT con undervolt de -75mV y Power Limit a 130W).
   - **GPU Idle:** 18.0W en reposo.
   - **GPU Carga activa:** 105.0W - 122.0W en procesos activos (`python`, `torch`, `vmmem`, `ollama`, etc.) o alta carga.
   - **Plataforma base:** 60.0W base (placa madre, RAM DDR5, NVMe, refrigeración) + dinámica de CPU (`(cpuPct/100)*50W`).
   - **Fuente 80+ Gold:** Curva dinámica de eficiencia entre **81%** (idle ~85W DC) y **88.5%** (carga >= 220W DC).

4. **Tarifas Reales y Seguridad de Datos:**
   - **Tarifa por defecto:** **$265.0 CLP/kWh** (Tarifa real boleta CGE BT1 Residencial Cauquenes / Maule con IVA y transmisión).
   - **Flush continuo en cada tick:** Ejecuta `csvWriter.Flush()` cada 2 segundos para asegurar que no se pierdan datos si se cierra la consola bruscamente.
   - **Resumen horario automático** y resumen consolidado al presionar `Ctrl + C`.

---

## 🚀 Guía de Uso en Windows

### 1. Ejecución Básica
Abre PowerShell o el Símbolo del Sistema (CMD) en la carpeta donde se encuentra el binario:

```powershell
.\power_monitor.exe
```

### 2. Uso con LibreHardwareMonitor (Recomendado para máxima precisión)
1. Descarga e inicia **LibreHardwareMonitor** en Windows como Administrador.
2. En la barra superior, ve a **Options** > **Remote Web Server** > marca **Run** (por defecto escucha en el puerto `8085`).
3. Ejecuta el monitor:
   ```powershell
   .\power_monitor.exe
   ```
   El monitor detectará automáticamente el servidor en `http://localhost:8085/data.json` y cambiará la fuente a `LHM-FULL` o `LHM-GPU`.

### 3. Opciones y Parámetros Disponibles

| Bandera | Valor por defecto | Descripción |
| :--- | :--- | :--- |
| `-interval` | `2.0` | Intervalo de muestreo en segundos. |
| `-summary-mins` | `60` | Frecuencia del resumen periódico en minutos. |
| `-cost-kwh-clp` | `265.0` | Tarifa en CLP por kWh (CGE Cauquenes BT1). |
| `-usd-clp` | `960.0` | Tipo de cambio referencial USD/CLP. |
| `-log-file` | `power_telemetry.csv` | Archivo CSV continuo (vacío para desactivar). |
| `-lhm-url` | `http://localhost:8085/data.json` | URL del servidor JSON de LibreHardwareMonitor. |
| `-quiet` | `false` | Silencia los ticks de 2s y solo muestra resúmenes. |

#### Ejemplos de comandos:
- **Modo silencioso (solo resúmenes horarios):**
  ```powershell
  .\power_monitor.exe -quiet
  ```
- **Cambiar tarifa o archivo CSV:**
  ```powershell
  .\power_monitor.exe -cost-kwh-clp 275.5 -log-file "D:\logs\entrenamiento_energia.csv"
  ```
- **Conectar a LHM en otra IP o puerto:**
  ```powershell
  .\power_monitor.exe -lhm-url "http://127.0.0.1:8085/data.json"
  ```

---

## 🛠️ Recompilación desde Linux (WSL / Servidor de compilación)

Si realizas cambios en `models/m01-transformer/scripts/utils/power_monitor_windows.go`, recompila el ejecutable con:

```bash
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o /mnt/d/Estuding/power_monitor.exe models/m01-transformer/scripts/utils/power_monitor_windows.go
```
