@echo off
REM Install PC Dashboard Monitor to Windows Startup
set "EXE_DIR=%~dp0"
set "EXE_PATH=%EXE_DIR%PC-Dashboard-Monitor.exe"
set "SHORTCUT_NAME=PC Dashboard Monitor"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Startup') + '\%SHORTCUT_NAME%.lnk'); $s.TargetPath = '%EXE_PATH:\=\%'; $s.WorkingDirectory = '%EXE_DIR:\=\%'; $s.WindowStyle = 7; $s.Description = 'PC Dashboard Monitor - Sensor Collector'; $s.Save()"

echo.
echo [OK] %SHORTCUT_NAME% added to Windows Startup.
echo [INFO] The app will start minimized on next boot.
pause
