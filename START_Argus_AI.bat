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

echo [*] Launching Professional Studio on http://localhost:12189
echo [*] Opening browser...
start http://localhost:12189

:: Run Streamlit in headless mode to keep it clean
streamlit run GUI\app.py --server.port 12189 --server.headless true

pause
