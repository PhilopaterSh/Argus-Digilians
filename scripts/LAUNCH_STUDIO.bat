@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Argus Security Framework - Studio Launcher
color 0A

echo ========================================================
echo        ARGUS SECURITY STUDIO - LAUNCHER
echo ========================================================
echo.

:: --- Resolve project root (scripts/ is one level down) ---
set "PROJECT_ROOT=%~dp0.."
pushd "%PROJECT_ROOT%"
set "PROJECT_ROOT=%CD%"
popd

:: --- Argument Support ---
set "ARG_CHOICE=%~1"

:: 1. Check & Start Ollama
echo [*] Checking AI Engine (Ollama)...
set "OLLAMA_MODE=GPU"

if /I "%ARG_CHOICE%"=="C" goto :force_cpu
if /I "%ARG_CHOICE%"=="R" goto :clean_restart
if /I "%ARG_CHOICE%"=="G" goto :check_running

echo [?] Troubleshooting: If you have GPU errors (CUDA), choose an option:
echo     [G] Standard GPU Mode (Default)
echo     [R] Clean Restart Ollama (Fixes most CUDA errors)
echo     [C] Force CPU Mode (Slow but 100%% Stable)
choice /C GRC /T 5 /D G /M "Selection: "

if errorlevel 3 goto :force_cpu
if errorlevel 2 goto :clean_restart
goto :check_running

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
start "" "ollama app.exe"
timeout /t 8 >nul
goto :check_ssh

:check_running
tasklist | findstr /I "ollama" >NUL
if %errorlevel% neq 0 (
    echo [!] Ollama is NOT running. Starting now...
    start "" "ollama app.exe"
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

:: 3. Verify virtual environment
echo [*] Checking virtual environment...
if not exist "%PROJECT_ROOT%\Argus_venv\Scripts\activate.bat" (
    echo [ERROR] Virtual Environment missing at %PROJECT_ROOT%\Argus_venv!
    echo [ERROR] Run INSTALL.bat from the project root first.
    pause & exit /b 1
)

:: 4. Set environment
set "PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\Argus_venv\Lib\site-packages;%PYTHONPATH%"
set "TRANSFORMERS_VERBOSITY=error"
set "STREAM_LOG_LEVEL=error"
set "PYTHONWARNINGS=ignore"

:: 5. Launch dashboard
echo [*] Activating environment and launching Dashboard...
echo [INFO] The browser will open automatically. Please wait 10 seconds.

cd /d "%PROJECT_ROOT%"
start http://localhost:12199
Argus_venv\Scripts\python.exe -m streamlit run app/GUI/dashboard.py --server.port 12199 --server.headless true --server.enableCORS false --server.enableXsrfProtection false

pause
