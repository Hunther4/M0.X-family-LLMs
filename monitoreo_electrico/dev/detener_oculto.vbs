Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "taskkill /F /IM power_monitor.exe", 0, True
Set WshShell = Nothing
