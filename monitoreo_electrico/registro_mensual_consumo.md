# 📊 Registro Oficial de Consumo Eléctrico y Control de Presupuesto

- **Comuna / Red:** Cauquenes, Región del Maule, Chile (CGE Distribución BT1 Residencial c/ IVA y peajes).
- **Tarifa Base Calibrada:** **$265.0 CLP / kWh**.
- **Perfil de Hardware:**
  - GPU: AMD Radeon RX 9060 XT (16 GB) con Undervolt de -75 mV y Power Limit limitado a 130 W (-30%).
  - CPU: AMD Ryzen (AM5) con PBO Curve Optimizer negativo (-30 a -35) y límite térmico fijado en 85 °C.
  - Plataforma: AM5 DDR5 + NVMe Gen4 (~60W en reposo).
  - Fuente de poder: Corsair RM850 80+ Gold (eficiencia dinámica 81% en idle a 88.5% en carga).
- **Meta Estricta Actual:** **Tope reajustado a $4.500 CLP para la segunda quincena de Noviembre (15 al 30 de Noviembre)**.
- **Estado Actual del Presupuesto (al 24/11 cerrado):** Acumulado gastado **$2.958 CLP** | Saldo restante **$1.542 CLP** para la quincena (25 al 30 de Noviembre).
- **Cuota Diaria Promedio Restante:** **~$257 CLP / día** (6 días restantes; permite ~4 a 5 horas diarias de uso mixto).

---

## 📅 Registro Diario (Segunda Quincena: 15 al 30 de Noviembre 2026)

| Fecha | Tiempo de Uso | Actividad Principal | Energía (kWh) | Costo Diario (CLP) | Acumulado Mes (CLP) | Estado del Presupuesto |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **15/11/2026** | **5 h 31 min** | Entrenamiento MoE 20M, benchmarks, Minecraft 70 FPS y reposo | **0.6723 kWh** | **$178 CLP** | **$178 CLP** | 🟢 **Excelente** (Dentro de la cuota diaria) |
| **16/11/2026** | **8 h 46 min** | Madrugada (anime/juego/chat) + Tarde/Noche (uso general y reposo) | **1.0890 kWh** | **$288 CLP** | **$466 CLP** | 🟢 **Muy Bueno** (Jornada extendida; en meta) |
| **17/11/2026** *(Cerrado)* | **2 h 42 min** | God of War (1h 51m) + Preparación y estructura presentación histórica (51m) | **0.4959 kWh** | **$131 CLP** | **$597 CLP** | 🟢 **Sobresaliente** (Solo 36% de la cuota diaria usada) |
| **18/11/2026** *(Cerrado)* | **8 h 23 min** | Madrugada (HTML interactivo y PDF, 4h 28m) + Tarde/Noche (ofimática y anime, 3h 55m) | **1.0983 kWh** | **$291 CLP** | **$888 CLP** | 🟢 **Excelente** (Dentro de la cuota diaria de ~$350 CLP) |
| **19/11/2026** *(Cerrado)* | **4 h 34 min** | Sesión tarde/noche (juego y uso general, 180W promedio) | **0.8249 kWh** | **$219 CLP** | **$1.107 CLP** | 🟢 **Excelente** (Muy por debajo del tope de $301 CLP) |
| **20/11/2026** *(Cerrado)* | **6 h 55 min** | Madrugada (2h 53m) + Tarde/Noche juego (4h 02m, 188W promedio) | **1.3001 kWh** | **$345 CLP** | **$1.451 CLP** | 🟡 **Pasado leve** (+$44 CLP sobre la cuota de $301 CLP) |
| **21/11/2026** *(Cerrado)* | **15 h 29 min** | Madrugada juego (5h) + Tarde modding (4h 48m) + Noche gaming Cyberpunk (5h 41m, 159W) | **2.6379 kWh** | **$699 CLP** | **$2.150 CLP** | 🟠 **Jornada maratónica** (Triple sesión; el undervolt amortiguó el costo a ~$44/h. Saldo quincenal aún controlado) |
| **22/11/2026** *(Cerrado)* | **7 h 54 min** | Madrugada JWE2 (3h 13m) + Tarde/Noche modding Cyberpunk y optimizaciones (4h 41m, 178W prom.) | **1.4180 kWh** | **$376 CLP** | **$2.526 CLP** | 🟢 **Controlado** (Jornada completa mixta; amortiguada por reposos y undervolt) |
| **23/11/2026** *(Madrugada)* | **3 h 09 min** | Sesión nocturna Cyberpunk 2077 (Penthouse, pruebas mods y crafting, 205W prom.) | **0.6490 kWh** | **$172 CLP** | **$2.698 CLP** | 🟢 **Excelente** (Cierre de madrugada; $172 CLP en más de 3h de gaming continuo) |
| **24/11/2026** *(Cerrado)* | **8 h 13 min** | Jornada continua tarde/noche: uso liviano/escritorio y carga GPU nocturna (119.3W prom.) | **0.9807 kWh** | **$260 CLP** | **$2.958 CLP** | 🟢 **En Meta** (Dentro de la cuota diaria; monitoreo LHM 100% continuo) |

---

## 🧰 Herramientas de Monitoreo en esta Carpeta

Para los próximos 1 a 3 meses de reposo de los modelos de IA, tienes dos opciones autónomas e independientes en este directorio:

### 1. Opción Windows Nativa (Recomendada para uso diario sin abrir WSL)
- **Ejecutable:** [`power_monitor.exe`](file:///mnt/d/Estuding/monitoreo_electrico/power_monitor.exe)
- **Uso:** Haz doble clic o abre PowerShell en `D:\Estuding\monitoreo_electrico` y ejecuta:
  ```powershell
  .\power_monitor.exe
  ```
  *(Recomendado: abre LibreHardwareMonitor con Web Server en el puerto 8085 para leer vatios reales de GPU y CPU. Sin LHM, el monitor usa estimaciones y no detecta juegos ni cargas dentro de WSL)*.
- **Ventaja:** Consume menos de 5 MB de RAM y vacía la telemetría en `power_telemetry.csv` continuamente. Cada fila incluye `step_wh`; al reiniciar recupera el total consumido hoy desde el CSV y a medianoche imprime el resumen diario.
- **Calibración:** `-wall-scale 1.08` ajusta la lectura AC si un medidor de pared marca distinto; `-extra-wall-w 12` suma monitor y periféricos.

### 2. Opción Linux / WSL2
- **Script:** [`dev/monitor_setup_power.py`](file:///mnt/d/Estuding/monitoreo_electrico/dev/monitor_setup_power.py)
- **Uso:**
  ```bash
  python3 dev/monitor_setup_power.py
  ```
- **Ventaja:** Conexión directa al sensor `amd-smi` en WSL2 sin dependencias pesadas.

---

## 📈 Proyecciones y Reglas de Oro para Mantener la Meta ($6.000 – $6.500 CLP)

1. **Tope de tiempo:** Mantener el uso diario en un máximo de **4 a 5 horas** de uso mixto.
2. **Juegos:** Mantener siempre el bloqueo de **70 FPS** en juegos como Minecraft con shaders para evitar que la GPU trabaje forzada a 130W continuos.
3. **Plan de energía de Windows:** Mantener en **Equilibrado** (Balanced) con suspensión automática de pantalla a los 10-15 minutos y del equipo a los 30-45 minutos.
