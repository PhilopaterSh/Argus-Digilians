@echo off
setlocal
cd /d "%~dp0"
title Argus Security Framework - Studio (Web GUI)
color 0A

echo ========================================================
echo        ARGUS SECURITY STUDIO - WEB GUI
echo ========================================================
echo.

:: 1. Ensure Ollama (AI engine) is running
echo [*] Checking AI Engine (Ollama)...
tasklist | findstr /I "ollama" >NUL
if %errorlevel% neq 0 (
    echo [!] Ollama not running. Starting...
    start "" "ollama app.exe"
    timeout /t 8 >nul
) else (
    echo [OK] AI Engine online.
)

:: 2. Ensure WSL/Kali SSH bridge is up
echo [*] Checking WSL SSH bridge...
powershell -Command "if ((Test-NetConnection -ComputerName 127.0.0.1 -Port 22 -ErrorAction SilentlyContinue).TcpTestSucceeded) { exit 0 } else { exit 1 }" >NUL 2>&1
if %errorlevel% neq 0 (
    echo [!] SSH bridge down. Starting sshd inside Kali...
    wsl -d kali-linux -u root bash -c "mkdir -p /run/sshd && /usr/sbin/sshd"
    timeout /t 2 >nul
) else (
    echo [OK] SSH bridge active.
)

:: 3. Launch Streamlit GUI (this folder IS the project root)
echo [*] Launching Web Interface at http://localhost:12199 ...
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
set "PYTHONWARNINGS=ignore"
set "STREAMLIT_LOG_LEVEL=error"

start http://localhost:12199
python -m streamlit run "GUI\app.py" --server.port 12199 --server.headless true --server.enableCORS false --server.enableXsrfProtection false

pause
