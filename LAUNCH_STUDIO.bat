@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Argus Security Framework - Studio Launcher
color 0A

echo ========================================================
echo        🚀 ARGUS SECURITY STUDIO - LAUNCHER
echo ========================================================
echo.

:: 1. Check & Start Ollama
echo [*] Checking AI Engine (Ollama)...
tasklist | findstr /I "ollama" >NUL
if %errorlevel% neq 0 (
    echo [!] Ollama is NOT running. Starting now...
    start "" "ollama app.exe"
    timeout /t 5 >nul
) else (
    echo [OK] AI Engine is Online.
)

:: 2. Check & Start WSL SSH (The Bridge)
echo [*] Checking WSL Bridge (SSH)...
powershell -Command "if ((Test-NetConnection -ComputerName 127.0.0.1 -Port 22 -ErrorAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }" >NUL 2>&1
if %errorlevel% neq 0 (
    echo [!] SSH Bridge is down. Attempting to start in Kali...
    wsl -d kali-linux -u root service ssh start
    timeout /t 2 >nul
) else (
    echo [OK] SSH Bridge is Active.
)

:: 3. Launching Studio
echo [*] Activating Environment and Launching Web Interface...
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual Environment missing! Run INSTALL_EVERYTHING.bat first.
    pause & exit /b
)

echo [*] Opening Browser at http://localhost:12199 ...
start http://localhost:12199

:: Run Streamlit
set "PYTHONPATH=%~dp0;%~dp0.venv\Lib\site-packages;%PYTHONPATH%"
.venv\Scripts\python.exe -m streamlit run GUI\app.py --server.port 12199 --server.headless true

pause
