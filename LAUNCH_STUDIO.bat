@echo off
setlocal enabledelayedexpansion
cd /d ""%~dp0""
title Argus Security Framework - Studio Launcher
color 0A

echo ========================================================
echo        ?? ARGUS SECURITY STUDIO - LAUNCHER
echo ========================================================
echo.

:: 1. Check & Start Ollama
echo [*] Checking AI Engine (Ollama)...
set ""OLLAMA_MODE=GPU""

echo [?] Troubleshooting: If you have GPU errors (CUDA), choose an option:
echo     [G] Standard GPU Mode (Default)
echo     [R] Clean Restart Ollama (Fixes most CUDA errors)
echo     [C] Force CPU Mode (Slow but 100%% Stable)
choice /C GRC /T 5 /D G /M ""Selection: ""

if errorlevel 3 goto :force_cpu
if errorlevel 2 goto :clean_restart
goto :check_running

:force_cpu
echo [!] Forcing CPU Mode...
set ""CUDA_VISIBLE_DEVICES=-1""
set ""OLLAMA_MODE=CPU""
:: Continue to clean restart to ensure variables take effect
:clean_restart
echo [*] Performing Clean Restart of Ollama...
taskkill /F /IM ""ollama app.exe"" >nul 2>&1
taskkill /F /IM ""ollama.exe"" >nul 2>&1
timeout /t 2 >nul
start """" ""ollama app.exe""
timeout /t 8 >nul
goto :check_ssh

:check_running
tasklist | findstr /I ""ollama"" >NUL
if %%errorlevel%% neq 0 (
    echo [!] Ollama is NOT running. Starting now...
    start """" ""ollama app.exe""
    timeout /t 10 >nul
) else (
    echo [OK] AI Engine is Online (%%OLLAMA_MODE%% Mode).
)

:check_ssh
:: 2. Check & Start WSL SSH (The Bridge)
echo [*] Checking WSL Bridge (SSH)...
powershell -Command ""if ((Test-NetConnection -ComputerName 127.0.0.1 -Port 22 -ErrorAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }"" >NUL 2>&1
if %%errorlevel%% neq 0 (
    echo [!] SSH Bridge is down. Attempting to start in Kali...
    wsl -d kali-linux -u root bash -c ""mkdir -p /run/sshd && /usr/sbin/sshd""
    timeout /t 2 >nul
) else (
    echo [OK] SSH Bridge is Active.
)

:: 3. Launching Studio
echo [*] Activating Environment and Launching Web Interface...
if not exist ""Argus_venv\Scripts\activate.bat"" (
    echo [ERROR] Virtual Environment missing! Run INSTALL_EVERYTHING.bat first.
    pause ^& exit /b
)

echo [*] Launching Streamlit Server...
echo [INFO] Silencing library noise for faster startup...
echo [INFO] The browser will open automatically. Please wait 10 seconds.

:: Set Environment Variables to silence noise
set ""PYTHONPATH=%%~dp0;%%~dp0Argus_venv\Lib\site-packages;%%PYTHONPATH%%""
set ""TRANSFORMERS_VERBOSITY=error""
set ""STREAMLIT_LOG_LEVEL=error""
set ""PYTHONWARNINGS=ignore""

start http://localhost:12199
Argus_venv\Scripts\python.exe -m streamlit run GUI\app.py --server.port 12199 --server.headless true --server.enableCORS false --server.enableXsrfProtection false

pause
