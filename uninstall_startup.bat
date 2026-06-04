@echo off
REM Remove PC Dashboard Monitor from Windows Startup
set "SHORTCUT_NAME=PC Dashboard Monitor"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\%SHORTCUT_NAME%.lnk"

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo [OK] %SHORTCUT_NAME% removed from Windows Startup.
) else (
    echo [INFO] Startup shortcut not found: %SHORTCUT_PATH%
)
pause
