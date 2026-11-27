package main

import (
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
	gpuIdleWatts           = 18.0  // Consumo en reposo medido con undervolt
	baseSystemWatts        = 60.0  // Plataforma base: CPU moderna, placa madre, DDR5, NVMe, refrigeración
	TH32CS_SNAPPROCESS     = 0x00000002
)

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
	hasGPU      bool
	hasCPU      bool
	hasActivity bool
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

// Detección nativa de procesos en Windows vía Toolhelp32
func detectActiveComputeProcess() bool {
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

	targets := []string{
		"python", "torch", "accelerate", "vllm", "train", "ollama",
		"llama", "deepspeed", "wslhost", "vmmem", "ffmpeg",
	}

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

	// 1. Potencia GPU
	if (inGPU || strings.Contains(label, "gpu")) && (strings.Contains(label, "power") || strings.Contains(label, "package") || strings.Contains(label, "total") || strings.Contains(label, "core")) {
		if w, ok := parseLHMFloat(node.Value, "W"); ok && w > 0 {
			// Priorizar Package / Total sobre Core
			if strings.Contains(label, "package") || strings.Contains(label, "total") || !tel.hasGPU {
				tel.gpuWatts = w
				tel.hasGPU = true
			}
		}
	}

	// 2. Potencia CPU
	if (inCPU || strings.Contains(label, "cpu")) && (strings.Contains(label, "package") || strings.Contains(label, "total") || strings.Contains(label, "core") || inPowers) {
		if w, ok := parseLHMFloat(node.Value, "W"); ok && w > 0 {
			if strings.Contains(label, "package") || strings.Contains(label, "total") || !tel.hasCPU {
				tel.cpuWatts = w
				tel.hasCPU = true
			}
		}
	}

	// 3. Actividad / Carga GPU
	if (inGPU || strings.Contains(label, "gpu")) && (inLoad || strings.Contains(label, "load") || strings.Contains(label, "core") || strings.Contains(label, "d3d")) {
		if pct, ok := parseLHMFloat(node.Value, "%"); ok {
			tel.gpuActivity = pct
			tel.hasActivity = true
		}
	}

	for i := range node.Children {
		parseLHMNode(&node.Children[i], inGPU, inCPU, inPowers, inLoad, tel)
	}
}

// Lectura de LibreHardwareMonitor Web Server con soporte de localhost y 127.0.0.1
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
		if tel.hasGPU || tel.hasCPU {
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

// Cálculo de potencia combinando telemetría de LHM y fallback calibrado
func computePower(
	cpuPct float64,
	lhmTel lhmTelemetry,
	lhmOK bool,
) (gpuW, sysW, wallW float64, source string) {
	if lhmOK && lhmTel.hasGPU && lhmTel.gpuWatts > 0 {
		gpuW = lhmTel.gpuWatts
		if gpuW > gpuCapWatts {
			gpuW = gpuCapWatts
		}
		source = "LHM-GPU"
	} else {
		// Fallback heurístico calibrado para el usuario
		active := detectActiveComputeProcess() || cpuPct > 20.0
		if active {
			// Carga activa calibrada (105W - 122W proporcional)
			gpuW = 105.0 + (cpuPct/100.0)*17.0
			if gpuW > 122.0 {
				gpuW = 122.0
			}
			source = "EST-LOAD"
		} else {
			gpuW = gpuIdleWatts
			source = "EST-IDLE"
		}
		if gpuW > gpuCapWatts {
			gpuW = gpuCapWatts
		}
	}

	// Plataforma base: 60W + dinámica de CPU (o CPU Package real de LHM)
	if lhmOK && lhmTel.hasCPU && lhmTel.cpuWatts > 0 {
		sysW = 35.0 + lhmTel.cpuWatts
		if source == "LHM-GPU" {
			source = "LHM-FULL"
		}
	} else {
		sysW = baseSystemWatts + (cpuPct/100.0)*50.0
	}

	dcTotal := gpuW + sysW
	wallW = dcTotal / psuEfficiency(dcTotal)
	return gpuW, sysW, wallW, source
}

func printHourlySummary(hourNum int, hourElapsed time.Duration, hourJoules, totalJoules, costKWhCLP float64) {
	hourKWh := hourJoules / 3_600_000.0
	hourCLP := hourKWh * costKWhCLP
	hourAvgW := 0.0
	if hourElapsed.Seconds() > 0 {
		hourAvgW = hourJoules / hourElapsed.Seconds()
	}

	totKWh := totalJoules / 3_600_000.0
	totCLP := totKWh * costKWhCLP

	nowStr := time.Now().Format("2006-01-02 15:04:05")
	fmt.Println("\n" + strings.Repeat("=", 86))
	fmt.Printf("⏰ RESUMEN HORARIO #%d  |  %s\n", hourNum, nowStr)
	fmt.Printf("   • Última hora (%.1f min):  %.5f kWh  |  Prom: %5.1f W  |  Costo: $%6.2f CLP\n",
		hourElapsed.Minutes(), hourKWh, hourAvgW, hourCLP)
	fmt.Printf("   • Acumulado total:          %.5f kWh  |  Costo Total:      $%6.2f CLP\n",
		totKWh, totCLP)
	fmt.Println(strings.Repeat("=", 86))
}

func main() {
	intervalSec := flag.Float64("interval", 2.0, "Intervalo de muestreo en segundos")
	summaryMins := flag.Int("summary-mins", 60, "Intervalo de resumen periódico en minutos (defecto: 60)")
	costCLPKWh := flag.Float64("cost-kwh-clp", defaultCauquenesCLPKWh, "Tarifa CLP por kWh (CGE Cauquenes BT1 con IVA y peajes)")
	logFile := flag.String("log-file", "power_telemetry.csv", "Ruta del CSV continuo de salida (vacío para desactivar)")
	lhmURL := flag.String("lhm-url", "http://localhost:8085/data.json", "URL de LibreHardwareMonitor Web Server")
	quiet := flag.Bool("quiet", false, "Ocultar ticks de 2s y mostrar solo resúmenes periódicos")
	flag.Parse()

	httpClient := &http.Client{Timeout: 500 * time.Millisecond}

	var csvWriter *csv.Writer
	var csvFile *os.File
	if *logFile != "" {
		if dir := filepath.Dir(*logFile); dir != "" && dir != "." {
			_ = os.MkdirAll(dir, 0o755)
		}
		f, err := os.OpenFile(*logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
		if err == nil {
			csvFile = f
			csvWriter = csv.NewWriter(f)
			info, _ := f.Stat()
			if info != nil && info.Size() == 0 {
				_ = csvWriter.Write([]string{"timestamp", "elapsed_sec", "cpu_pct", "gpu_w", "sys_w", "wall_w", "source", "total_kwh", "cost_clp"})
				csvWriter.Flush()
			}
		} else {
			fmt.Printf("⚠️ Advertencia: No se pudo abrir CSV '%s': %v\n", *logFile, err)
		}
	}

	fmt.Println(strings.Repeat("=", 86))
	fmt.Println("⚡ DEMONIO NATIVO DE TELEMETRÍA ELÉCTRICA (WINDOWS - GO)")
	fmt.Printf("🇨🇱 Tarifa: Cauquenes / Maule (CGE BT1) -> $%.1f CLP/kWh\n", *costCLPKWh)
	fmt.Printf("⏱️  Muestreo: %.1fs | Resumen cada: %d min | LHM: %s\n", *intervalSec, *summaryMins, *lhmURL)
	if *logFile != "" {
		fmt.Printf("📁 Telemetría continua CSV: %s (Flush periódico activo)\n", *logFile)
	}
	fmt.Println(strings.Repeat("=", 86))
	if !*quiet {
		fmt.Printf("%10s | %5s | %7s | %6s | %8s | %9s | %9s | %9s\n",
			"Tiempo", "CPU%", "GPU(W)", "PC(W)", "Pared(W)", "Fuente", "kWh Acum", "CLP ($)")
		fmt.Println(strings.Repeat("-", 86))
	}

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	sampleInterval := time.Duration(*intervalSec * float64(time.Second))
	sampleTicker := time.NewTicker(sampleInterval)
	defer sampleTicker.Stop()

	hourlyTicker := time.NewTicker(time.Duration(*summaryMins) * time.Minute)
	defer hourlyTicker.Stop()

	startTime := time.Now()
	lastSampleTime := startTime
	hourStartTime := startTime

	prevCPU, _ := readCPUSample()

	// Muestra inicial
	lhmTel, lhmErr := fetchLHM(httpClient, *lhmURL)
	_, _, prevWallW, _ := computePower(0, lhmTel, lhmErr == nil)

	var totalJoules float64
	var hourStartJoules float64
	hourCount := 1

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
			fmt.Println("\n" + strings.Repeat("=", 86))
			fmt.Println("🛑 MONITOR DETENIDO — RESUMEN CONSOLIDADO DE LA SESIÓN")
			fmt.Printf("⏱️  Duración total: %.2f horas (%.1f min)\n", totalElapsed/3600.0, totalElapsed/60.0)
			fmt.Printf("🔌 Potencia promedio pared: %.1f W\n", avgW)
			fmt.Printf("⚡ Energía total: %.6f kWh (%.2f kJ)\n", totKWh, totalJoules/1000.0)
			fmt.Printf("🇨🇱 Costo final (Cauquenes CGE BT1): $%.2f CLP\n", totCLP)
			fmt.Println(strings.Repeat("=", 86))
			return

		case <-hourlyTicker.C:
			now := time.Now()
			hourElapsed := now.Sub(hourStartTime)
			hourJoules := totalJoules - hourStartJoules
			printHourlySummary(hourCount, hourElapsed, hourJoules, totalJoules, *costCLPKWh)
			hourStartTime = now
			hourStartJoules = totalJoules
			hourCount++
			if csvWriter != nil {
				csvWriter.Flush()
			}

		case now := <-sampleTicker.C:
			dt := now.Sub(lastSampleTime).Seconds()
			lastSampleTime = now

			currCPU, err := readCPUSample()
			cpuPct := 0.0
			if err == nil {
				cpuPct = calcCPUPercent(prevCPU, currCPU)
				prevCPU = currCPU
			}

			lhmTel, lhmErr := fetchLHM(httpClient, *lhmURL)
			gpuW, sysW, wallW, src := computePower(cpuPct, lhmTel, lhmErr == nil)

			// Integración trapezoidal de energía
			stepJoules := ((prevWallW + wallW) / 2.0) * dt
			totalJoules += stepJoules
			prevWallW = wallW

			totKWh := totalJoules / 3_600_000.0
			totCLP := totKWh * (*costCLPKWh)
			elapsed := int(now.Sub(startTime).Seconds())
			hrs := elapsed / 3600
			mins := (elapsed % 3600) / 60
			secs := elapsed % 60

			if !*quiet {
				fmt.Printf("%02d:%02d:%02d | %5.1f | %6.1fW | %5.1fW | %7.1fW | %9s | %9.5f | $%8.2f\n",
					hrs, mins, secs, cpuPct, gpuW, sysW, wallW, src, totKWh, totCLP)
			}

			// Escritura y Flush inmediato para evitar pérdida ante cierre de ventana en Windows
			if csvWriter != nil {
				_ = csvWriter.Write([]string{
					now.Format(time.RFC3339),
					fmt.Sprintf("%.1f", now.Sub(startTime).Seconds()),
					fmt.Sprintf("%.1f", cpuPct),
					fmt.Sprintf("%.1f", gpuW),
					fmt.Sprintf("%.1f", sysW),
					fmt.Sprintf("%.1f", wallW),
					src,
					fmt.Sprintf("%.6f", totKWh),
					fmt.Sprintf("%.3f", totCLP),
				})
				csvWriter.Flush()
			}
		}
	}
}
