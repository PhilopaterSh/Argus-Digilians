@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Argus Security Framework - Studio Launcher
color 0A

echo ========================================================
echo        ?? ARGUS SECURITY STUDIO - LAUNCHER
echo ========================================================
echo.

:: --- Argument Support ---
set "ARG_CHOICE=%~1"

:: 1. Check & Start Ollama
echo [*] Checking AI Engine (Ollama)...
set "OLLAMA_MODE=GPU"

if defined ARG_CHOICE (
    if /I "%ARG_CHOICE%"=="C" goto :force_cpu
    if /I "%ARG_CHOICE%"=="R" goto :clean_restart
    if /I "%ARG_CHOICE%"=="G" goto :check_running
) else (
    rem No argument provided; default to GPU mode non-interactively
    set "ARG_CHOICE=G"
    goto :check_running
)

:force_cpu
echo [!] Forcing CPU Mode...
set "CUDA_VISIBLE_DEVICES=-1"
set "OLLAMA_MODE=CPU"
goto :clean_restart

:clean_restart
echo [*] Performing Clean Restart of Ollama...
taskkill /F /IM "ollama app.exe" >nul 2>&1
taskkill /F /IM "ollama.exe" >nul 2>&1
timeout /t 2 >nul
start "" "ollama app.exe" >nul 2>&1
timeout /t 8 >nul
goto :check_ssh

:check_running
tasklist | findstr /I "ollama" >NUL
if %errorlevel% neq 0 (
    echo [!] Ollama is NOT running. Starting now...
    start "" "ollama app.exe" >nul 2>&1
    timeout /t 10 >nul
) else (
    echo [OK] AI Engine is Online - %OLLAMA_MODE% Mode.
)

:check_ssh
:: 2. Check & Start WSL SSH (The Bridge)
echo [*] Checking WSL Bridge (SSH)...
powershell -Command "if ((Test-NetConnection -ComputerName 127.0.0.1 -Port 22 -ErrorAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }" >NUL 2>&1
if %errorlevel% neq 0 (
    echo [!] SSH Bridge is down. Attempting to start in Kali...
    wsl -d kali-linux -u root bash -c "mkdir -p /run/sshd && /usr/sbin/sshd"
    timeout /t 2 >nul
) else (
    echo [OK] SSH Bridge is Active.
)

:: 3. Launching Studio
echo [*] Activating Environment and Launching Web Interface...
if not exist "Argus_venv\Scripts\activate.bat" (
    echo [ERROR] Virtual Environment missing! Run INSTALL_EVERYTHING.bat first.
    pause & exit /b
)

echo [*] Launching Streamlit Server...
echo [INFO] Silencing library noise for faster startup...
echo [INFO] The browser will open automatically. Please wait 10 seconds.

:: Set Environment Variables to silence noise
set "PYTHONPATH=%~dp0;%~dp0Argus_venv\Lib\site-packages;%PYTHONPATH%"
set "TRANSFORMERS_VERBOSITY=error"
set "STREAM_LOG_LEVEL=error"
set "PYTHONWARNINGS=ignore"

start http://localhost:8501
..\Argus_venv\Scripts\python.exe -m streamlit run ..\app\GUI\gui_app.py --server.port 8501 --server.headless true --server.enableCORS false --server.enableXsrfProtection false

pause
