@echo off
title Argus AI Security Studio - Master Launcher
color 0A
echo ========================================================
echo        🛡️ ARGUS AI SECURITY STUDIO - STARTING...
echo ========================================================
echo.

:: 1. Check if Ollama is running
echo [*] Checking Intelligence Engine (Ollama)...
tasklist /FI "IMAGENAME eq ollama app.exe" 2>NUL | find /I /N "ollama app.exe">NUL
if errorlevel 1 (
    echo [!] Ollama is NOT running. Attempting to start...
    start "" "ollama app.exe"
    timeout /t 5 >nul
) else (
    echo [OK] Intelligence Engine is ONLINE.
)

:: 2. Activate Environment and Launch GUI
echo [*] Activating Python Environment...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo [ERROR] Virtual Environment not found in Root. Please run Master_Installer.bat first.
    pause
    exit
)

echo [*] Verifying Dependencies...
python -c "import paramiko; print('[OK] Paramiko is verified.')"
if %errorlevel% neq 0 (
    echo [ERROR] Dependency verification failed!
    pause
    exit
)

echo [*] Launching Professional Studio on http://localhost:12199
echo [*] Opening browser...
start http://localhost:12199

:: Set PYTHONPATH to ensure all modules are found correctly
set "PYTHONPATH=%~dp0;%~dp0.venv\Lib\site-packages;%PYTHONPATH%"

:: Run Streamlit using the specific python from venv to ensure correct package loading
.venv\Scripts\python.exe -m streamlit run GUI\app.py --server.port 12199 --server.headless true

pause
