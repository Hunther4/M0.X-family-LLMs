# ⚡ Monitor Nativo de Energía y Telemetría Eléctrica para Windows

**Binario:** `power_monitor.exe` (compilado en Go, nativo PE32+ para x86-64 Windows)  
**Código fuente:** [`dev/power_monitor_windows.go`](file:///mnt/d/Estuding/monitoreo_electrico/dev/power_monitor_windows.go)

---

## 🎯 Características Principales

1. **100% Nativo de Windows (sin dependencias Linux):**
   - Sin lecturas a `/proc` ni `/sys`.
   - CPU medida con `GetSystemTimes` de `kernel32.dll` vía `syscall` y `syscall.Filetime`.
   - Detección de procesos de cómputo con `CreateToolhelp32Snapshot`.

2. **Integración con LibreHardwareMonitor (LHM) — recomendada para precisión real:**
   - Se conecta al Web Server de LHM en `http://127.0.0.1:8085/data.json` por defecto.
   - Extrae **GPU Package/Total Power**, **CPU Package Power** y **GPU Activity (%)**.
   - Descarta lecturas fuera de rango (GPU < 600 W, CPU < 500 W) y registra una vez el nombre del sensor elegido.
   - Si LHM está activo pero no publica vatios de GPU, usa la actividad de GPU para estimar.

3. **Fallback heurístico cuando LHM no está disponible:**
   - **GPU cap:** 130 W (RX 9060 XT con undervolt -75 mV y power limit a 130 W).
   - **GPU idle:** 25 W (media medida en reposo; antes eran 18 W).
   - **GPU carga:** 115 W solo si detecta un proceso inequívoco (`ollama`, `vllm`, `llama`, `ffmpeg`).
   - **Plataforma:** 35 W base (placa, RAM DDR5, NVMe, ventiladores) + CPU estimada `25 W + 50 W * cpuPct/100` → 60 W en reposo y 110 W a CPU plena.
   - **Fuente 80+ Gold:** curva de eficiencia entre **81%** (idle, ~85 W DC) y **88.5%** (carga, >= 220 W DC).
   - **Limitaciones honestas:** este fallback NO detecta juegos (p. ej. `javaw`) ni cargas dentro de WSL; `vmmem`/`wslhost` se excluyeron porque están siempre presentes y daban falsos positivos. Una instancia de Ollama abierta pero sin inferir también puede dar falso positivo. Para medir juegos o WSL con exactitud, usa LHM.

4. **Contabilidad diaria real:**
   - Cada fila guarda `run_id`, `step_wh` (energía del intervalo por trapecio) y totales de sesión.
   - El total diario se obtiene sumando `step_wh` por fecha; es exacto aunque haya reinicios o cortes.
   - Al arrancar, el monitor lee el CSV y recupera lo ya consumido hoy.
   - A medianoche imprime un **resumen diario** y reinicia el contador.
   - Si cambia el esquema del CSV, el archivo anterior se conserva como `*.bak-YYYYMMDD-HHMMSS` y se crea uno nuevo con la cabecera actual.

5. **Tarifa real y seguridad de datos:**
   - **Tarifa por defecto:** **265.0 CLP/kWh** (CGE BT1 Residencial Cauquenes / Maule, con IVA y transmisión).
   - **Flush en cada tick:** `csvWriter.Flush()` cada 2 s; si se cierra la consola bruscamente se pierde como máximo el último intervalo.
   - **Resumen periódico** (cada 60 min por defecto) y resumen de sesión + día al salir con `Ctrl + C`.

---

## 🚀 Guía de Uso en Windows

### 1. Ejecución básica
Abre PowerShell o CMD en `D:\Estuding\monitoreo_electrico`:

```powershell
.\power_monitor.exe
```

### 2. Uso con LibreHardwareMonitor (máxima precisión)
1. Descarga e inicia **LibreHardwareMonitor** como Administrador.
2. **Options > Remote Web Server > Run** (puerto `8085` por defecto).
3. Ejecuta el monitor. Verás `LHM` o `LHM-ACT` en la columna `Fuente` y el nombre de los sensores elegidos una vez al inicio.
4. Para que LHM arranque solo, agrégalo a **Task Scheduler** al iniciar sesión. No se configura automáticamente.

### 3. Opciones y parámetros

| Bandera | Valor por defecto | Descripción |
| :--- | :--- | :--- |
| `-interval` | `2.0` | Intervalo de muestreo en segundos. Debe ser > 0. |
| `-summary-mins` | `60` | Frecuencia del resumen periódico en minutos. Debe ser > 0. |
| `-cost-kwh-clp` | `265.0` | Tarifa en CLP por kWh (CGE Cauquenes BT1). |
| `-log-file` | `power_telemetry.csv` | CSV continuo. Vacío para desactivar (el total diario queda solo en memoria). |
| `-lhm-url` | `http://127.0.0.1:8085/data.json` | URL del JSON de LHM. Vacío para desactivar LHM. |
| `-wall-scale` | `1.0` | Factor de calibración AC del PC. Si un medidor de pared lee 10% más, usa `1.10`. Debe ser > 0. |
| `-extra-wall-w` | `0.0` | Vatios AC extra (monitor, periféricos, luces). Se suman después de la eficiencia de la fuente. |
| `-quiet` | `false` | Silencia los ticks y deja solo resúmenes y avisos. |

#### Ejemplos

- **Modo silencioso (solo resúmenes):**
  ```powershell
  .\power_monitor.exe -quiet
  ```
- **Tarifa y archivo CSV personalizados:**
  ```powershell
  .\power_monitor.exe -cost-kwh-clp 275.5 -log-file "D:\logs\entrenamiento_energia.csv"
  ```
- **LHM en otra IP/puerto:**
  ```powershell
  .\power_monitor.exe -lhm-url "http://192.168.1.50:8085/data.json"
  ```
- **Calibración con medidor de pared y periféricos:**
  ```powershell
  .\power_monitor.exe -wall-scale 1.08 -extra-wall-w 12
  ```
- **Forzar solo estimación (sin LHM):**
  ```powershell
  .\power_monitor.exe -lhm-url ""
  ```

---

## 📄 Columnas del CSV

| Columna | Descripción |
| :--- | :--- |
| `run_id` | Identificador de la ejecución (`YYYYMMDDTHHMMSS-PID`). |
| `timestamp` | Fecha/hora local en RFC3339. |
| `elapsed_sec` | Segundos desde el inicio de esta ejecución. |
| `cpu_pct` | Uso de CPU (0–100). |
| `gpu_w` | Potencia DC estimada/medida de la GPU. |
| `sys_w` | Potencia DC estimada/medida del resto del PC (placa + CPU). |
| `wall_w` | Potencia AC en la pared: PC / eficiencia × `wall-scale` + `extra-wall-w`. |
| `gpu_activity_pct` | Actividad de GPU (0–100); `-1` si no está disponible. |
| `source` | `LHM`, `LHM-ACT`, `EST-LOAD` o `EST-IDLE`. |
| `cpu_source` | `LHM` (paquete CPU real) o `EST` (estimado). |
| `step_wh` | Energía del intervalo por trapecio (Wh). **Sumar por fecha = consumo diario exacto.** |
| `total_kwh` | Total acumulado de esta ejecución (kWh), no del día. |
| `cost_clp` | Costo acumulado de esta ejecución (CLP), no del día. |

Para el día, agrupa por la fecha local de `timestamp` y suma `step_wh`. El monitor ya lo hace al arrancar y en el resumen de medianoche.

---

## 🛠️ Recompilación

Desde esta carpeta (`D:\Estuding\monitoreo_electrico`):

```powershell
go vet dev\power_monitor_windows.go
go build -ldflags="-s -w" -o power_monitor.exe dev\power_monitor_windows.go
```

Desde Linux/WSL, para el binario Windows:

```bash
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o power_monitor.exe dev/power_monitor_windows.go
```

Para el binario Linux (mismo esquema de CSV y contabilidad diaria):

```bash
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o dev/power_monitor_linux dev/power_monitor_linux.go
```
