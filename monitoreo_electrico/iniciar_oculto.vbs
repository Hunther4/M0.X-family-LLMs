Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Estuding\monitoreo_electrico"
WshShell.Run "power_monitor.exe -log-file power_telemetry_go.csv -quiet", 0, False
Set WshShell = Nothing
