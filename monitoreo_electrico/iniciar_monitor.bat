@echo off
title Monitoreo de Consumo Electrico - Cauquenes (Windows)
cd /d "%~dp0"

echo ======================================================================
echo   ⚡ MONITOR DE CONSUMO ELECTRICO NATIVO EN WINDOWS (Go PE32+)
echo   Comuna: Cauquenes, Región del Maule (Tarifa: $265.0 CLP/kWh)
echo   Meta mensual: $5.000 - $6.000 CLP (Tope diario: ~$160-$180 CLP)
echo ======================================================================
echo.

rem Verificar si LibreHardwareMonitor esta corriendo
tasklist /fi "imagename eq LibreHardwareMonitor.exe" 2>NUL | find /i /n "LibreHardwareMonitor.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] LibreHardwareMonitor detectado en ejecucion.
) else (
    echo [AVISO] LibreHardwareMonitor no esta corriendo.
    echo Si quieres medicion exacta de vatios de CPU y GPU:
    echo Ejecuta como Administrador: LibreHardwareMonitor\LibreHardwareMonitor.exe
    echo y activa: Options ^> Remote Web Server ^> Run (puerto 8085).
    echo.
    echo Continuando con modelo de estimacion heuristica...
)

echo.
echo Telemetria guardandose en: power_telemetry_go.csv
echo Presiona Ctrl+C en cualquier momento para ver el resumen final y salir.
echo ======================================================================
echo.

power_monitor.exe -log-file power_telemetry_go.csv

pause
