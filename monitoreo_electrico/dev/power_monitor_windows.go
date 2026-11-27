package main

import (
	"bufio"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

// Constantes de calibración de hardware y tarifas para el usuario
const (
	defaultCauquenesCLPKWh = 265.0 // CGE BT1 Residencial Cauquenes / Maule (c/ IVA y peajes)
	gpuCapWatts            = 130.0 // Límite de potencia estricto RX 9060 XT (-75mV undervolt, -30% power cap)
	gpuIdleWatts           = 25.0  // Consumo GPU en reposo medido (media real 25W; antes 18W)
	gpuFallbackLoadWatts   = 115.0 // Fallback de carga GPU solo cuando hay un proceso GPU inequívoco
	platformBaseWatts      = 35.0  // Placa madre, DDR5, NVMe y refrigeración (sin CPU)
	cpuIdleWatts           = 25.0  // CPU en reposo dentro del modelo de plataforma
	cpuLoadDeltaWatts      = 50.0  // Diferencia CPU idle -> carga (modelo 60W idle / 110W carga)
	maxSampleGapSec        = 60.0  // Acota dt tras suspensión/bloqueo para no inflar la energía
	TH32CS_SNAPPROCESS     = 0x00000002
)

var csvHeader = []string{
	"run_id", "timestamp", "elapsed_sec", "cpu_pct", "gpu_w", "sys_w", "wall_w",
	"gpu_activity_pct", "source", "cpu_source", "step_wh", "total_kwh", "cost_clp",
}

// DLL y llamadas de Win32 (kernel32.dll)
var (
	modkernel32                  = syscall.NewLazyDLL("kernel32.dll")
	procGetSystemTimes           = modkernel32.NewProc("GetSystemTimes")
	procCreateToolhelp32Snapshot = modkernel32.NewProc("CreateToolhelp32Snapshot")
	procProcess32FirstW          = modkernel32.NewProc("Process32FirstW")
	procProcess32NextW           = modkernel32.NewProc("Process32NextW")
	procCloseHandle              = modkernel32.NewProc("CloseHandle")
)

// Estructuras de Win32
type cpuSample struct {
	idle   uint64
	kernel uint64
	user   uint64
}

type processEntry32 struct {
	dwSize              uint32
	cntUsage            uint32
	th32ProcessID       uint32
	th32DefaultHeapID   uintptr
	th32ModuleID        uint32
	cntThreads          uint32
	th32ParentProcessID uint32
	pcPriClassBase      int32
	dwFlags             uint32
	szExeFile           [260]uint16
}

// Estructura de árbol de LibreHardwareMonitor Web Server (/data.json)
type lhmNode struct {
	Text     string    `json:"Text"`
	Value    string    `json:"Value"`
	Children []lhmNode `json:"Children"`
}

type lhmTelemetry struct {
	gpuWatts    float64
	cpuWatts    float64
	gpuActivity float64
	gpuSensor   string
	cpuSensor   string
	hasGPU      bool
	hasCPU      bool
	hasActivity bool
}

func clamp(v, lo, hi float64) float64 {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}

func filetimeToUint64(ft syscall.Filetime) uint64 {
	return (uint64(ft.HighDateTime) << 32) | uint64(ft.LowDateTime)
}

// Lectura de CPU nativa de Windows con GetSystemTimes de kernel32.dll
func readCPUSample() (cpuSample, error) {
	var idleTime, kernelTime, userTime syscall.Filetime
	r1, _, err := procGetSystemTimes.Call(
		uintptr(unsafe.Pointer(&idleTime)),
		uintptr(unsafe.Pointer(&kernelTime)),
		uintptr(unsafe.Pointer(&userTime)),
	)
	if r1 == 0 {
		return cpuSample{}, err
	}
	return cpuSample{
		idle:   filetimeToUint64(idleTime),
		kernel: filetimeToUint64(kernelTime),
		user:   filetimeToUint64(userTime),
	}, nil
}

// En Windows GetSystemTimes, kernelTime incluye idleTime
func calcCPUPercent(prev, curr cpuSample) float64 {
	kernelDelta := curr.kernel - prev.kernel
	userDelta := curr.user - prev.user
	idleDelta := curr.idle - prev.idle

	totalDelta := kernelDelta + userDelta
	if totalDelta == 0 {
		return 0.0
	}
	if totalDelta < idleDelta {
		return 0.0
	}
	busyDelta := totalDelta - idleDelta
	pct := (float64(busyDelta) / float64(totalDelta)) * 100.0
	if pct < 0.0 {
		return 0.0
	}
	if pct > 100.0 {
		return 100.0
	}
	return pct
}

// Detección de procesos con señal GPU inequívoca. python.exe no sirve:
// un script de CPU y uno de GPU se ven igual. LHM es la vía recomendada.
func detectActiveGPUProcess() bool {
	hSnap, _, _ := procCreateToolhelp32Snapshot.Call(TH32CS_SNAPPROCESS, 0)
	if syscall.Handle(hSnap) == syscall.InvalidHandle {
		return false
	}
	defer procCloseHandle.Call(hSnap)

	var entry processEntry32
	entry.dwSize = uint32(unsafe.Sizeof(entry))

	r1, _, _ := procProcess32FirstW.Call(hSnap, uintptr(unsafe.Pointer(&entry)))
	if r1 == 0 {
		return false
	}

	// Solo nombres que suelen implicar trabajo GPU. vmmem/wslhost se excluyen:
	// están presentes con WSL abierto aunque la GPU esté en reposo.
	targets := []string{"ollama", "vllm", "llama", "ffmpeg"}

	for {
		name := syscall.UTF16ToString(entry.szExeFile[:])
		lower := strings.ToLower(name)
		for _, t := range targets {
			if strings.Contains(lower, t) {
				return true
			}
		}
		r1, _, _ = procProcess32NextW.Call(hSnap, uintptr(unsafe.Pointer(&entry)))
		if r1 == 0 {
			break
		}
	}
	return false
}

// Extractor de números con unidades en formato LHM ("123.4 W" o "123,4 W")
func parseLHMFloat(val, unit string) (float64, bool) {
	val = strings.TrimSpace(val)
	if !strings.HasSuffix(val, unit) {
		return 0, false
	}
	numStr := strings.TrimSpace(strings.TrimSuffix(val, unit))
	numStr = strings.ReplaceAll(numStr, ",", ".")
	num, err := strconv.ParseFloat(numStr, 64)
	if err != nil {
		return 0, false
	}
	return num, true
}

func parseLHMNode(node *lhmNode, inGPU, inCPU, inPowers, inLoad bool, tel *lhmTelemetry) {
	label := strings.ToLower(node.Text)

	// Contexto de hardware
	if strings.Contains(label, "gpu") || strings.Contains(label, "radeon") ||
		strings.Contains(label, "geforce") || strings.Contains(label, "nvidia") {
		inGPU = true
	}
	if strings.Contains(label, "cpu") || strings.Contains(label, "ryzen") ||
		strings.Contains(label, "intel") || strings.Contains(label, "processor") {
		inCPU = true
	}
	if strings.Contains(label, "power") {
		inPowers = true
	}
	if strings.Contains(label, "load") {
		inLoad = true
	}

	// 1. Potencia GPU. Límites de cordura para descartar sensores absurdos.
	if (inGPU || strings.Contains(label, "gpu")) && (strings.Contains(label, "power") || strings.Contains(label, "package") || strings.Contains(label, "total") || strings.Contains(label, "core")) {
		if w, ok := parseLHMFloat(node.Value, "W"); ok && w > 0 && w < 600 {
			preferred := strings.Contains(label, "package") || strings.Contains(label, "total")
			if preferred || !tel.hasGPU {
				tel.gpuWatts = w
				tel.gpuSensor = node.Text
				tel.hasGPU = true
			}
		}
	}

	// 2. Potencia CPU. Preferir Package/Total sobre Core.
	if (inCPU || strings.Contains(label, "cpu")) && (strings.Contains(label, "package") || strings.Contains(label, "total") || strings.Contains(label, "core") || inPowers) {
		if w, ok := parseLHMFloat(node.Value, "W"); ok && w > 0 && w < 500 {
			preferred := strings.Contains(label, "package") || strings.Contains(label, "total")
			if preferred || !tel.hasCPU {
				tel.cpuWatts = w
				tel.cpuSensor = node.Text
				tel.hasCPU = true
			}
		}
	}

	// 3. Actividad / Carga GPU
	if (inGPU || strings.Contains(label, "gpu")) && (inLoad || strings.Contains(label, "load") || strings.Contains(label, "core") || strings.Contains(label, "d3d")) {
		if pct, ok := parseLHMFloat(node.Value, "%"); ok {
			tel.gpuActivity = clamp(pct, 0, 100)
			tel.hasActivity = true
		}
	}

	for i := range node.Children {
		parseLHMNode(&node.Children[i], inGPU, inCPU, inPowers, inLoad, tel)
	}
}

// Lectura de LibreHardwareMonitor Web Server con soporte de localhost y 127.0.0.1.
// Acepta también solo actividad: permite estimar la GPU si el sensor de vatios no aparece.
func fetchLHM(client *http.Client, primaryURL string) (lhmTelemetry, error) {
	if primaryURL == "" {
		return lhmTelemetry{}, fmt.Errorf("no LHM URL provided")
	}

	urls := []string{primaryURL}
	if strings.Contains(primaryURL, "localhost") {
		urls = append(urls, strings.Replace(primaryURL, "localhost", "127.0.0.1", 1))
	} else if strings.Contains(primaryURL, "127.0.0.1") {
		urls = append(urls, strings.Replace(primaryURL, "127.0.0.1", "localhost", 1))
	}

	for _, u := range urls {
		resp, err := client.Get(u)
		if err != nil {
			continue
		}
		body, err := io.ReadAll(resp.Body)
		_ = resp.Body.Close()
		if err != nil {
			continue
		}

		var root lhmNode
		if err := json.Unmarshal(body, &root); err != nil {
			continue
		}

		var tel lhmTelemetry
		parseLHMNode(&root, false, false, false, false, &tel)
		if tel.hasGPU || tel.hasCPU || tel.hasActivity {
			return tel, nil
		}
	}

	return lhmTelemetry{}, fmt.Errorf("LHM Web Server uncontactable")
}

// Curva dinámica de eficiencia de fuente 80+ Gold (81% a 88.5%)
func psuEfficiency(dcWatts float64) float64 {
	if dcWatts <= 85.0 {
		return 0.81
	}
	if dcWatts >= 220.0 {
		return 0.885
	}
	return 0.81 + ((dcWatts-85.0)/(220.0-85.0))*(0.885-0.81)
}

// Cálculo de potencia combinando telemetría de LHM y fallback calibrado.
// gpu_source: LHM, LHM-ACT, EST-LOAD o EST-IDLE. cpu_source: LHM o EST.
func computePower(
	cpuPct float64,
	lhmTel lhmTelemetry,
	lhmOK bool,
	wallScale, extraWallW float64,
) (gpuW, sysW, wallW float64, source, cpuSource string) {
	switch {
	case lhmOK && lhmTel.hasGPU && lhmTel.gpuWatts > 0:
		gpuW = clamp(lhmTel.gpuWatts, 0, gpuCapWatts)
		source = "LHM"
	case lhmOK && lhmTel.hasActivity:
		act := clamp(lhmTel.gpuActivity, 0, 100)
		gpuW = gpuIdleWatts + (act/100.0)*(gpuCapWatts-gpuIdleWatts)
		source = "LHM-ACT"
	case detectActiveGPUProcess():
		gpuW = gpuFallbackLoadWatts
		source = "EST-LOAD"
	default:
		gpuW = gpuIdleWatts
		source = "EST-IDLE"
	}

	// Plataforma: misma base con o sin LHM. 35W placa+RAM+NVMe + CPU.
	cpuSource = "EST"
	if lhmOK && lhmTel.hasCPU && lhmTel.cpuWatts > 0 {
		sysW = platformBaseWatts + lhmTel.cpuWatts
		cpuSource = "LHM"
	} else {
		sysW = platformBaseWatts + cpuIdleWatts + (cpuPct/100.0)*cpuLoadDeltaWatts
	}

	dcTotal := gpuW + sysW
	wallW = (dcTotal / psuEfficiency(dcTotal) * wallScale) + extraWallW
	return gpuW, sysW, wallW, source, cpuSource
}

func printPeriodicSummary(num int, periodElapsed time.Duration, periodJoules, sessionJoules, dayJoules, costKWhCLP float64) {
	periodKWh := periodJoules / 3_600_000.0
	periodCLP := periodKWh * costKWhCLP
	periodAvgW := 0.0
	if periodElapsed.Seconds() > 0 {
		periodAvgW = periodJoules / periodElapsed.Seconds()
	}

	sessionKWh := sessionJoules / 3_600_000.0
	sessionCLP := sessionKWh * costKWhCLP
	dayKWh := dayJoules / 3_600_000.0
	dayCLP := dayKWh * costKWhCLP

	nowStr := time.Now().Format("2006-01-02 15:04:05")
	fmt.Println("\n" + strings.Repeat("=", 86))
	fmt.Printf("⏰ RESUMEN PERIÓDICO #%d  |  %s\n", num, nowStr)
	fmt.Printf("   • Último período (%.1f min): %.5f kWh | Prom: %5.1f W | Costo: $%6.2f CLP\n",
		periodElapsed.Minutes(), periodKWh, periodAvgW, periodCLP)
	fmt.Printf("   • Sesión actual:             %.5f kWh | Costo: $%6.2f CLP\n",
		sessionKWh, sessionCLP)
	fmt.Printf("   • Hoy (desde CSV):           %.5f kWh | Costo: $%6.2f CLP\n",
		dayKWh, dayCLP)
	fmt.Println(strings.Repeat("=", 86))
}

func printDailySummary(dayKey string, dayJoules, costKWhCLP float64) {
	kWh := dayJoules / 3_600_000.0
	fmt.Println("\n" + strings.Repeat("=", 86))
	fmt.Printf("📅 RESUMEN DIARIO %s\n", dayKey)
	fmt.Printf("   • Consumo del día: %.6f kWh | Costo: $%.2f CLP\n", kWh, kWh*costKWhCLP)
	fmt.Println(strings.Repeat("=", 86))
}

// Abre el CSV y rota el archivo si el esquema cambió, para no mezclar columnas.
func openTelemetryCSV(path string) (*csv.Writer, *os.File, error) {
	if dir := filepath.Dir(path); dir != "" {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return nil, nil, err
		}
	}

	if st, err := os.Stat(path); err == nil && st.Size() > 0 {
		f, err := os.Open(path)
		if err != nil {
			return nil, nil, err
		}
		line, _ := bufio.NewReader(f).ReadString('\n')
		_ = f.Close()
		if strings.TrimSpace(line) != strings.Join(csvHeader, ",") {
			backup := path + ".bak-" + time.Now().Format("20060102-150405")
			if _, statErr := os.Stat(backup); statErr == nil {
				backup += "-1"
			}
			if err := os.Rename(path, backup); err != nil {
				return nil, nil, fmt.Errorf("esquema CSV anterior y no se pudo respaldar: %w", err)
			}
			fmt.Printf("ℹ️ CSV con esquema anterior guardado en: %s\n", backup)
		}
	} else if err != nil && !os.IsNotExist(err) {
		return nil, nil, err
	}

	f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return nil, nil, err
	}
	w := csv.NewWriter(f)
	if st, err := f.Stat(); err == nil && st.Size() == 0 {
		if err := w.Write(csvHeader); err != nil {
			_ = f.Close()
			return nil, nil, err
		}
		w.Flush()
		if err := w.Error(); err != nil {
			_ = f.Close()
			return nil, nil, err
		}
	}
	return w, f, nil
}

// Suma step_wh de las filas cuya fecha local coincide con dayKey. Permite
// retomar el acumulado diario tras reiniciar el monitor sin archivo de estado.
func loadDayJoules(path, dayKey string) (float64, error) {
	f, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return 0, nil
		}
		return 0, err
	}
	defer f.Close()

	r := csv.NewReader(f)
	r.FieldsPerRecord = -1
	header, err := r.Read()
	if err != nil {
		return 0, nil
	}
	tsIdx, whIdx := -1, -1
	for i, h := range header {
		switch h {
		case "timestamp":
			tsIdx = i
		case "step_wh":
			whIdx = i
		}
	}
	if tsIdx < 0 || whIdx < 0 {
		return 0, nil
	}

	var wh float64
	for {
		rec, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue
		}
		if tsIdx >= len(rec) || whIdx >= len(rec) {
			continue
		}
		ts, err := time.Parse(time.RFC3339, rec[tsIdx])
		if err != nil {
			continue
		}
		if ts.Local().Format("2006-01-02") != dayKey {
			continue
		}
		v, err := strconv.ParseFloat(rec[whIdx], 64)
		if err != nil {
			continue
		}
		wh += v
	}
	return wh * 3600.0, nil
}

func validateFlags(intervalSec float64, summaryMins int, costCLPKWh, wallScale, extraWallW float64) {
	if intervalSec <= 0 {
		fmt.Fprintf(os.Stderr, "❌ -interval debe ser > 0 (recibido: %v)\n", intervalSec)
		os.Exit(2)
	}
	if summaryMins <= 0 {
		fmt.Fprintf(os.Stderr, "❌ -summary-mins debe ser > 0 (recibido: %d)\n", summaryMins)
		os.Exit(2)
	}
	if costCLPKWh < 0 {
		fmt.Fprintf(os.Stderr, "❌ -cost-kwh-clp no puede ser negativo (recibido: %v)\n", costCLPKWh)
		os.Exit(2)
	}
	if wallScale <= 0 {
		fmt.Fprintf(os.Stderr, "❌ -wall-scale debe ser > 0 (recibido: %v)\n", wallScale)
		os.Exit(2)
	}
	if extraWallW < 0 {
		fmt.Fprintf(os.Stderr, "❌ -extra-wall-w no puede ser negativo (recibido: %v)\n", extraWallW)
		os.Exit(2)
	}
}

func main() {
	intervalSec := flag.Float64("interval", 2.0, "Intervalo de muestreo en segundos")
	summaryMins := flag.Int("summary-mins", 60, "Intervalo de resumen periódico en minutos (defecto: 60)")
	costCLPKWh := flag.Float64("cost-kwh-clp", defaultCauquenesCLPKWh, "Tarifa CLP por kWh (CGE Cauquenes BT1 con IVA y peajes)")
	logFile := flag.String("log-file", "power_telemetry.csv", "Ruta del CSV continuo de salida (vacío para desactivar)")
	lhmURL := flag.String("lhm-url", "http://127.0.0.1:8085/data.json", "URL de LibreHardwareMonitor Web Server (vacío para desactivar)")
	wallScale := flag.Float64("wall-scale", 1.0, "Factor de calibración contra medidor de pared (AC estimado * factor)")
	extraWallW := flag.Float64("extra-wall-w", 0.0, "Watts AC extra fuera de la torre (monitor, periféricos, standby)")
	quiet := flag.Bool("quiet", false, "Ocultar ticks de muestreo y mostrar solo resúmenes")
	flag.Parse()

	validateFlags(*intervalSec, *summaryMins, *costCLPKWh, *wallScale, *extraWallW)

	httpClient := &http.Client{Timeout: 500 * time.Millisecond}

	var csvWriter *csv.Writer
	var csvFile *os.File
	if *logFile != "" {
		w, f, err := openTelemetryCSV(*logFile)
		if err != nil {
			fmt.Printf("⚠️ CSV desactivado: %v\n", err)
		} else {
			csvWriter, csvFile = w, f
		}
	}

	startTime := time.Now()
	runID := fmt.Sprintf("%s-%d", startTime.Format("20060102T150405"), os.Getpid())
	dayKey := startTime.Local().Format("2006-01-02")
	var dayJoules float64
	if csvWriter != nil {
		var err error
		dayJoules, err = loadDayJoules(*logFile, dayKey)
		if err != nil {
			fmt.Printf("⚠️ No se pudo leer el acumulado de hoy: %v\n", err)
			dayJoules = 0
		}
	}

	fmt.Println(strings.Repeat("=", 86))
	fmt.Println("⚡ DEMONIO NATIVO DE TELEMETRÍA ELÉCTRICA (WINDOWS - GO)")
	fmt.Printf("🆔 Run: %s\n", runID)
	fmt.Printf("🇨🇱 Tarifa: Cauquenes / Maule (CGE BT1) -> $%.1f CLP/kWh\n", *costCLPKWh)
	lhmLabel := *lhmURL
	if lhmLabel == "" {
		lhmLabel = "desactivado"
	}
	fmt.Printf("⏱️  Muestreo: %.2fs | Resumen cada: %d min | LHM: %s\n", *intervalSec, *summaryMins, lhmLabel)
	fmt.Printf("🔌 Escala de pared: %.3f | Extra AC: %.1f W\n", *wallScale, *extraWallW)
	if *logFile != "" {
		fmt.Printf("📁 Telemetría continua CSV: %s (flush por tick)\n", *logFile)
	} else {
		fmt.Println("⚠️ CSV desactivado: el acumulado diario no persistirá entre ejecuciones.")
	}
	dayKWh := dayJoules / 3_600_000.0
	fmt.Printf("📅 Día local: %s | Hoy (CSV): %.6f kWh | $%.2f CLP\n", dayKey, dayKWh, dayKWh*(*costCLPKWh))
	fmt.Println(strings.Repeat("=", 86))
	if !*quiet {
		fmt.Printf("%10s | %5s | %7s | %6s | %8s | %11s | %9s | %9s\n",
			"Tiempo", "CPU%", "GPU(W)", "PC(W)", "Pared(W)", "Fuente", "Hoy kWh", "CLP hoy")
		fmt.Println(strings.Repeat("-", 86))
	}

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	sampleInterval := time.Duration(*intervalSec * float64(time.Second))
	sampleTicker := time.NewTicker(sampleInterval)
	defer sampleTicker.Stop()

	periodicTicker := time.NewTicker(time.Duration(*summaryMins) * time.Minute)
	defer periodicTicker.Stop()

	lastSampleTime := startTime
	periodStartTime := startTime

	prevCPU, _ := readCPUSample()

	var lhmTel lhmTelemetry
	var lhmErr error
	lhmOK := false
	if *lhmURL != "" {
		lhmTel, lhmErr = fetchLHM(httpClient, *lhmURL)
		lhmOK = lhmErr == nil
	}
	_, _, prevWallW, _, _ := computePower(0, lhmTel, lhmOK, *wallScale, *extraWallW)

	var totalJoules float64
	var periodStartJoules float64
	periodCount := 1
	lhmFails := 0
	lhmWarned := false
	sensorsLogged := false
	gapWarned := false

	for {
		select {
		case <-sigChan:
			now := time.Now()
			totalElapsed := now.Sub(startTime).Seconds()
			totKWh := totalJoules / 3_600_000.0
			totCLP := totKWh * (*costCLPKWh)
			avgW := 0.0
			if totalElapsed > 0 {
				avgW = totalJoules / totalElapsed
			}
			if csvWriter != nil {
				csvWriter.Flush()
				_ = csvFile.Close()
			}
			dayKWh := dayJoules / 3_600_000.0
			fmt.Println("\n" + strings.Repeat("=", 86))
			fmt.Println("🛑 MONITOR DETENIDO — RESUMEN CONSOLIDADO DE LA SESIÓN")
			fmt.Printf("🆔 Run: %s\n", runID)
			fmt.Printf("⏱️  Duración total: %.2f horas (%.1f min)\n", totalElapsed/3600.0, totalElapsed/60.0)
			fmt.Printf("🔌 Potencia promedio pared: %.1f W\n", avgW)
			fmt.Printf("⚡ Energía de esta sesión: %.6f kWh (%.2f kJ) | $%.2f CLP\n", totKWh, totalJoules/1000.0, totCLP)
			fmt.Printf("📅 Hoy (%s): %.6f kWh | $%.2f CLP\n", dayKey, dayKWh, dayKWh*(*costCLPKWh))
			if csvWriter == nil {
				fmt.Println("⚠️ Sin CSV: el total de hoy corresponde solo a esta sesión.")
			}
			fmt.Println(strings.Repeat("=", 86))
			return

		case <-periodicTicker.C:
			now := time.Now()
			periodElapsed := now.Sub(periodStartTime)
			periodJoules := totalJoules - periodStartJoules
			printPeriodicSummary(periodCount, periodElapsed, periodJoules, totalJoules, dayJoules, *costCLPKWh)
			periodStartTime = now
			periodStartJoules = totalJoules
			periodCount++
			if csvWriter != nil {
				csvWriter.Flush()
			}

		case now := <-sampleTicker.C:
			newDayKey := now.Local().Format("2006-01-02")
			if newDayKey != dayKey {
				printDailySummary(dayKey, dayJoules, *costCLPKWh)
				dayKey = newDayKey
				dayJoules = 0
			}

			dt := now.Sub(lastSampleTime).Seconds()
			lastSampleTime = now
			if dt > maxSampleGapSec {
				if !gapWarned {
					fmt.Printf("\n⚠️ Hueco de muestreo de %.0fs (suspensión/bloqueo); energía acotada a %.0fs.\n", dt, maxSampleGapSec)
					gapWarned = true
				}
				dt = maxSampleGapSec
			}

			currCPU, err := readCPUSample()
			cpuPct := 0.0
			if err == nil {
				cpuPct = calcCPUPercent(prevCPU, currCPU)
				prevCPU = currCPU
			}

			if *lhmURL != "" {
				lhmTel, lhmErr = fetchLHM(httpClient, *lhmURL)
				if lhmErr != nil {
					lhmFails++
					if !lhmWarned && lhmFails >= 5 {
						fmt.Println("\n⚠️ LHM no responde tras 5 intentos; usando estimación. Abre el Web Server en el puerto 8085.")
						lhmWarned = true
					}
				} else {
					if lhmWarned {
						fmt.Println("\n✅ LHM recuperado; usando telemetría real.")
					}
					lhmFails = 0
					lhmWarned = false
				}
			}
			lhmOK = *lhmURL != "" && lhmErr == nil
			if lhmOK && !sensorsLogged {
				fmt.Printf("\n🔎 Sensores LHM: GPU=%q CPU=%q\n", lhmTel.gpuSensor, lhmTel.cpuSensor)
				sensorsLogged = true
			}

			gpuW, sysW, wallW, src, cpuSrc := computePower(cpuPct, lhmTel, lhmOK, *wallScale, *extraWallW)

			// Integración trapezoidal de energía
			stepJoules := ((prevWallW + wallW) / 2.0) * dt
			totalJoules += stepJoules
			dayJoules += stepJoules
			prevWallW = wallW

			stepWh := stepJoules / 3600.0
			totKWh := totalJoules / 3_600_000.0
			totCLP := totKWh * (*costCLPKWh)
			dayKWh := dayJoules / 3_600_000.0
			dayCLP := dayKWh * (*costCLPKWh)
			elapsed := int(now.Sub(startTime).Seconds())
			hrs := elapsed / 3600
			mins := (elapsed % 3600) / 60
			secs := elapsed % 60

			if !*quiet {
				fmt.Printf("%02d:%02d:%02d | %5.1f | %6.1fW | %5.1fW | %7.1fW | %11s | %9.5f | $%8.2f\n",
					hrs, mins, secs, cpuPct, gpuW, sysW, wallW, src, dayKWh, dayCLP)
			}

			// Escritura y flush inmediato para evitar pérdida ante cierre de ventana en Windows
			if csvWriter != nil {
				activity := "-1"
				if lhmOK && lhmTel.hasActivity {
					activity = fmt.Sprintf("%.1f", clamp(lhmTel.gpuActivity, 0, 100))
				}
				_ = csvWriter.Write([]string{
					runID,
					now.Format(time.RFC3339),
					fmt.Sprintf("%.1f", now.Sub(startTime).Seconds()),
					fmt.Sprintf("%.1f", cpuPct),
					fmt.Sprintf("%.1f", gpuW),
					fmt.Sprintf("%.1f", sysW),
					fmt.Sprintf("%.1f", wallW),
					activity,
					src,
					cpuSrc,
					fmt.Sprintf("%.4f", stepWh),
					fmt.Sprintf("%.6f", totKWh),
					fmt.Sprintf("%.3f", totCLP),
				})
				csvWriter.Flush()
			}
		}
	}
}
