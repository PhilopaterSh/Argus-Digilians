@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Argus System Health Check
color 0E

echo ========================================================
echo        (o) ARGUS SYSTEM HEALTH DIAGNOSTICS
echo ========================================================
echo.

set HEALTHY=YES

:: 1. Check Python & Venv
echo [*] Checking Python Environment...
if exist ".venv\Scripts\python.exe" (
    echo [OK] Virtual Environment found at Root.
) else (
    echo [ERR] Virtual Environment ^(.venv^) MISSING at Root.
    set HEALTHY=NO
)

:: 2. Check Ollama
echo [*] Checking Ollama Engine...
:: Checking for the process without relying on exact tasklist filtering which can be flaky
tasklist | findstr /I "ollama" >NUL
if %errorlevel% neq 0 (
    echo [ERR] Ollama process is NOT running.
    set HEALTHY=NO
) else (
    echo [OK] Ollama Engine is ONLINE.
)

:: 3. Check WSL & Kali
echo [*] Checking WSL (Kali Linux)...
powershell -Command "if (wsl --list | Select-String 'kali-linux') { exit 0 } else { exit 1 }" >NUL 2>&1
if %errorlevel% neq 0 (
    echo [ERR] Kali Linux distro is NOT detected in WSL.
    set HEALTHY=NO
) else (
    echo [OK] Kali Linux is detected in WSL.
)

:: 4. Check SSH Bridge (New Check)
echo [*] Checking SSH Bridge to WSL...
powershell -Command "if ((Test-NetConnection -ComputerName 127.0.0.1 -Port 22).TcpTestSucceeded) { exit 0 } else { exit 1 }" >NUL 2>&1
if %errorlevel% neq 0 (
    echo [ERR] SSH Bridge ^(Port 22^) is NOT accessible.
    set HEALTHY=NO
) else (
    echo [OK] SSH Bridge is ACTIVE.
)

echo.
echo --------------------------------------------------------
if "%HEALTHY%"=="YES" color 0A
if "%HEALTHY%"=="YES" echo [RESULT] SYSTEM IS HEALTHY AND READY!
if "%HEALTHY%"=="NO"  color 0C
if "%HEALTHY%"=="NO"  echo [RESULT] SYSTEM HAS ISSUES. PLEASE RUN Master_Installer.bat
echo --------------------------------------------------------
pause
