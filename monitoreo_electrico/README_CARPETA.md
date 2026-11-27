# ⚡ Sistema de Monitoreo Eléctrico y Telemetría

Bienvenido a la suite de telemetría y contabilidad de consumo eléctrico para el setup de cómputo (Cauquenes, Maule — Tarifa CGE BT1: $265.0 CLP/kWh).

Esta carpeta está organizada para máxima seguridad operativa, separando los ejecutables y lanzadores de producción del código fuente y los respaldos históricos.

---

## 📁 Estructura del Directorio

```text
D:\Estuding\monitoreo_electrico\
│
├── 🚀 ARCHIVOS OPERATIVOS PRINCIPALES (Producción)
│   ├── power_monitor.exe            <- Binario nativo Go x86-64 (ejecutándose en segundo plano)
│   ├── power_telemetry_go.csv       <- Telemetría activa en tiempo real (flush cada 2 seg)
│   ├── iniciar_monitor.bat          <- Lanzador con consola interactiva visible
│   ├── iniciar_oculto.vbs           <- Lanzador silencioso en segundo plano (sin ventana CMD)
│   ├── detener_monitor.bat          <- Script para detener de forma segura el monitor
│   ├── registro_mensual_consumo.md  <- Control presupuestario y registro de gastos en CLP
│   ├── LEEME_MONITOR_WINDOWS.md     <- Manual técnico completo del monitor Go
│   └── README_CARPETA.md            <- Este archivo (índice y estructura)
│
├── 🎛️ SENSORES Y HARDWARE
│   └── LibreHardwareMonitor\        <- Herramienta portable para lectura física de vatios GPU/CPU
│
├── 🗄️ HISTÓRICO Y BACKUPS
│   └── historico_telemetria\        <- Telemetrías archivadas y respaldos automáticos
│       ├── power_telemetry_go.csv.bak-20261116-030115
│       └── telemetria_2026-11-15.csv
│
└── 🛠️ DESARROLLO Y CÓDIGO FUENTE
    └── dev\                         <- Código fuente, scripts complementarios y utilidades
        ├── power_monitor_windows.go <- Código fuente del demonio nativo Windows (Go)
        ├── power_monitor_linux.go   <- Código fuente del demonio nativo Linux (Go)
        ├── power_monitor_linux      <- Binario compilado para Linux/WSL (ELF x86-64)
        ├── monitor_setup_power.py   <- Monitor legacy en Python (AMD-SMI / Linux)
        └── detener_oculto.vbs       <- Parada silenciosa de emergencia
```

---

## ⚠️ Reglas de Seguridad Operativa

1. **Monitor activo en tiempo real:**
   - `power_monitor.exe` se encuentra corriendo como demonio en Windows.
   - `power_telemetry_go.csv` está recibiendo escrituras continuas cada 2 segundos.
   - **No renombrar, mover ni eliminar** ninguno de estos dos archivos mientras el proceso esté activo.
2. **Cómo detener el monitor:**
   - Ejecuta `detener_monitor.bat` con doble clic. Confirmará que el proceso fue terminado limpiamente.
3. **Cómo iniciar el monitor:**
   - **Modo interactivo (recomendado si deseas ver estadísticas en vivo):** Doble clic a `iniciar_monitor.bat`.
   - **Modo silencioso (segundo plano):** Doble clic a `iniciar_oculto.vbs`.

---

## 📊 Integración con LibreHardwareMonitor (LHM)

Para obtener lecturas con precisión física de hardware:
1. Abre `LibreHardwareMonitor\LibreHardwareMonitor.exe` como Administrador.
2. En el menú superior: **Options > Remote Web Server > Run** (puerto `8085`).
3. El monitor Go detectará automáticamente la API web y medirá vatios reales de GPU Package y CPU Package.
4. Si LHM no está abierto, el monitor continuará funcionando mediante el modelo heurístico calibrado.

---

## 🛠️ Recompilación de Fuentes (Carpeta `dev/`)

Si se modifican los archivos `.go`:
- **Windows (PowerShell):**
  ```powershell
  go build -ldflags="-s -w" -o power_monitor.exe dev\power_monitor_windows.go
  ```
- **Desde WSL / Linux cruzado a Windows:**
  ```bash
  GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o power_monitor.exe dev/power_monitor_windows.go
  ```
