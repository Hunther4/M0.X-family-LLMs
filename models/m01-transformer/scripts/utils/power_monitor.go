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
)

const (
	defaultCauquenesCLPKWh = 265.0 // CGE BT1 Residencial Cauquenes (c/ IVA y transmisión)
	defaultUSDCLP          = 960.0
	gpuCapWatts            = 130.0 // Límite de potencia configurado en RX 9060 XT (-75mV)
	gpuIdleWatts           = 18.0
	baseSystemWatts        = 65.0
)

type cpuSample struct {
	idle  uint64
	total uint64
}

type lhmNode struct {
	Text     string    `json:"Text"`
	Value    string    `json:"Value"`
	Children []lhmNode `json:"Children"`
}

func readCPUSample() (cpuSample, error) {
	data, err := os.ReadFile("/proc/stat")
	if err != nil {
		return cpuSample{}, err
	}
	lines := strings.Split(string(data), "\n")
	if len(lines) == 0 {
		return cpuSample{}, fmt.Errorf("empty /proc/stat")
	}
	fields := strings.Fields(lines[0])
	if len(fields) < 5 || fields[0] != "cpu" {
		return cpuSample{}, fmt.Errorf("unexpected /proc/stat format")
	}

	var vals []uint64
	for _, f := range fields[1:] {
		v, err := strconv.ParseUint(f, 10, 64)
		if err != nil {
			continue
		}
		vals = append(vals, v)
	}

	var total uint64
	for _, v := range vals {
		total += v
	}
	idle := vals[3]
	if len(vals) > 4 {
		idle += vals[4] // iowait
	}
	return cpuSample{idle: idle, total: total}, nil
}

func calcCPUPercent(prev, curr cpuSample) float64 {
	totalDelta := curr.total - prev.total
	idleDelta := curr.idle - prev.idle
	if totalDelta == 0 {
		return 0.0
	}
	pct := (float64(totalDelta-idleDelta) / float64(totalDelta)) * 100.0
	if pct < 0 {
		return 0
	}
	if pct > 100 {
		return 100
	}
	return pct
}

// 1. Intenta leer sensor nativo de Linux (hwmon power1_average en microWatts)
func readLinuxHwmonGPUWatts() (float64, bool) {
	matches, err := filepath.Glob("/sys/class/drm/card*/device/hwmon/hwmon*/power1_average")
	if err != nil || len(matches) == 0 {
		return 0, false
	}
	for _, path := range matches {
		raw, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		uw, err := strconv.ParseFloat(strings.TrimSpace(string(raw)), 64)
		if err == nil && uw > 0 {
			return uw / 1_000_000.0, true
		}
	}
	return 0, false
}

// 2. Intenta leer LibreHardwareMonitor Web Server en Windows (ej: http://172.x.x.1:8085/data.json)
func readLHMJSONWatts(client *http.Client, url string) (float64, bool) {
	if url == "" {
		return 0, false
	}
	resp, err := client.Get(url)
	if err != nil {
		return 0, false
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return 0, false
	}
	var root lhmNode
	if err := json.Unmarshal(body, &root); err != nil {
		return 0, false
	}
	return findGPUPowerInLHM(root)
}

func findGPUPowerInLHM(node lhmNode) (float64, bool) {
	label := strings.ToLower(node.Text)
	if (strings.Contains(label, "gpu core") || strings.Contains(label, "gpu package") || strings.Contains(label, "gpu power")) &&
		strings.HasSuffix(node.Value, " W") {
		numStr := strings.TrimSpace(strings.TrimSuffix(node.Value, " W"))
		numStr = strings.ReplaceAll(numStr, ",", ".")
		if w, err := strconv.ParseFloat(numStr, 64); err == nil && w > 0 {
			return w, true
		}
	}
	for _, child := range node.Children {
		if w, ok := findGPUPowerInLHM(child); ok {
			return w, true
		}
	}
	return 0, false
}

// 3. Fallback calibrado inspeccionando /proc sin subprocesos y respetando el límite de 130W
func detectActiveWorkload() bool {
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return false
	}
	selfPID := strconv.Itoa(os.Getpid())
	keywords := []string{"train_sft", "train.py", "pretrain", "accelerate", "torchrun", "vllm"}

	for _, entry := range entries {
		if !entry.IsDir() || entry.Name() == selfPID {
			continue
		}
		if _, err := strconv.Atoi(entry.Name()); err != nil {
			continue
		}
		cmdBytes, err := os.ReadFile(filepath.Join("/proc", entry.Name(), "cmdline"))
		if err != nil || len(cmdBytes) == 0 {
			continue
		}
		cmd := strings.ToLower(strings.ReplaceAll(string(cmdBytes), "\x00", " "))
		for _, kw := range keywords {
			if strings.Contains(cmd, kw) {
				return true
			}
		}
	}
	return false
}

func psuEfficiency(dcWatts float64) float64 {
	// Curva realista 80+ Gold: ~81% en idle (<=85W DC) hasta ~88.5% en carga (>=220W DC)
	if dcWatts <= 85.0 {
		return 0.81
	}
	if dcWatts >= 220.0 {
		return 0.885
	}
	return 0.81 + ((dcWatts-85.0)/(220.0-85.0))*(0.885-0.81)
}

func computePower(cpuPct float64, lhmClient *http.Client, lhmURL string) (gpuW, sysW, wallW float64, source string) {
	if w, ok := readLinuxHwmonGPUWatts(); ok {
		gpuW = w
		source = "hwmon"
	} else if w, ok := readLHMJSONWatts(lhmClient, lhmURL); ok {
		gpuW = w
		source = "LHM"
	} else if detectActiveWorkload() {
		// Carga estimada bajo tope de 130W
		gpuW = 122.0 + (cpuPct/100.0)*8.0
		if gpuW > gpuCapWatts {
			gpuW = gpuCapWatts
		}
		source = "est-load"
	} else {
		gpuW = gpuIdleWatts
		source = "est-idle"
	}

	sysW = baseSystemWatts + (cpuPct/100.0)*50.0
	dcTotal := gpuW + sysW
	wallW = dcTotal / psuEfficiency(dcTotal)
	return gpuW, sysW, wallW, source
}

func printHourlySummary(hourNum int, hourElapsed time.Duration, hourJoules, totalJoules, costKWhCLP, costKWhUSD float64) {
	hourKWh := hourJoules / 3_600_000.0
	hourCLP := hourKWh * costKWhCLP
	hourUSD := hourKWh * costKWhUSD
	hourAvgW := 0.0
	if hourElapsed.Seconds() > 0 {
		hourAvgW = hourJoules / hourElapsed.Seconds()
	}

	totKWh := totalJoules / 3_600_000.0
	totCLP := totKWh * costKWhCLP
	totUSD := totKWh * costKWhUSD

	nowStr := time.Now().Format("2006-01-02 15:04:05")
	fmt.Println("\n" + strings.Repeat("=", 86))
	fmt.Printf("⏰ RESUMEN HORARIO #%d  |  %s\n", hourNum, nowStr)
	fmt.Printf("   • Última hora (%.1f min):  %.5f kWh  |  Prom: %5.1f W  |  Costo: $%6.2f CLP ($%.4f USD)\n",
		hourElapsed.Minutes(), hourKWh, hourAvgW, hourCLP, hourUSD)
	fmt.Printf("   • Acumulado total:          %.5f kWh  |  Costo Total:      $%6.2f CLP ($%.4f USD)\n",
		totKWh, totCLP, totUSD)
	fmt.Println(strings.Repeat("=", 86))
}

func main() {
	intervalSec := flag.Float64("interval", 2.0, "Intervalo de muestreo en segundos")
	summaryMins := flag.Int("summary-mins", 60, "Intervalo de resumen periódico en minutos (defecto: 60)")
	costCLPKWh := flag.Float64("cost-kwh-clp", defaultCauquenesCLPKWh, "Tarifa CLP por kWh (CGE Cauquenes BT1)")
	usdCLP := flag.Float64("usd-clp", defaultUSDCLP, "Tipo de cambio USD/CLP")
	logFile := flag.String("log-file", "power_telemetry.csv", "Ruta del CSV continuo (vacío para desactivar)")
	lhmURL := flag.String("lhm-url", "", "URL opcional de LibreHardwareMonitor (ej: http://172.24.0.1:8085/data.json)")
	quiet := flag.Bool("quiet", false, "Ocultar ticks cada 2s y mostrar solo los resúmenes cada 1 hora")
	flag.Parse()

	costUSDKWh := *costCLPKWh / *usdCLP
	httpClient := &http.Client{Timeout: 400 * time.Millisecond}

	var csvWriter *csv.Writer
	var csvFile *os.File
	if *logFile != "" {
		if err := os.MkdirAll(filepath.Dir(*logFile), 0o755); err == nil {
			f, err := os.OpenFile(*logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
			if err == nil {
				csvFile = f
				csvWriter = csv.NewWriter(f)
				info, _ := f.Stat()
				if info != nil && info.Size() == 0 {
					_ = csvWriter.Write([]string{"timestamp", "elapsed_sec", "cpu_pct", "gpu_w", "sys_w", "wall_w", "source", "total_kwh", "cost_clp"})
					csvWriter.Flush()
				}
			}
		}
	}

	fmt.Println(strings.Repeat("=", 86))
	fmt.Println("⚡ DEMONIO PERMANENTE DE TELEMETRÍA ELÉCTRICA (GO)")
	fmt.Printf("🇨🇱 Tarifa: Cauquenes / Maule (CGE BT1) -> $%.1f CLP/kWh (~$%.3f USD/kWh)\n", *costCLPKWh, costUSDKWh)
	fmt.Printf("⏱️  Muestreo: %.1fs | Resumen automático cada: %d min | CSV: %s\n", *intervalSec, *summaryMins, *logFile)
	fmt.Println(strings.Repeat("=", 86))
	if !*quiet {
		fmt.Printf("%10s | %5s | %7s | %6s | %8s | %8s | %9s | %9s\n",
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
	_, _, prevWallW, _ := computePower(0, httpClient, *lhmURL)

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
			totUSD := totKWh * costUSDKWh
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
			fmt.Printf("🇨🇱 Costo final (Cauquenes CGE BT1): $%.2f CLP ($%.4f USD)\n", totCLP, totUSD)
			fmt.Println(strings.Repeat("=", 86))
			return

		case <-hourlyTicker.C:
			now := time.Now()
			hourElapsed := now.Sub(hourStartTime)
			hourJoules := totalJoules - hourStartJoules
			printHourlySummary(hourCount, hourElapsed, hourJoules, totalJoules, *costCLPKWh, costUSDKWh)
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

			gpuW, sysW, wallW, src := computePower(cpuPct, httpClient, *lhmURL)

			// Integración trapezoidal
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
				fmt.Printf("%02d:%02d:%02d | %5.1f | %6.1fW | %5.1fW | %7.1fW | %8s | %9.5f | $%8.2f\n",
					hrs, mins, secs, cpuPct, gpuW, sysW, wallW, src, totKWh, totCLP)
			}

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
			}
		}
	}
}
