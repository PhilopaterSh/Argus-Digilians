@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Argus System Health Check
color 0E

echo ========================================================
echo        🔍 ARGUS SYSTEM HEALTH DIAGNOSTICS
echo ========================================================
echo.

set HEALTHY=YES

:: 1. Check Python & Venv
echo [*] Checking Python Environment...
if exist ".venv\Scripts\python.exe" goto venv_ok
echo [!!] Virtual Environment (.venv) MISSING at Root.
set HEALTHY=NO
goto check_ollama

:venv_ok
echo [OK] Virtual Environment found at Root.

:check_ollama
:: 2. Check Ollama
echo [*] Checking Ollama Engine...
tasklist /FI "IMAGENAME eq ollama app.exe" 2>NUL | find /I "ollama app.exe" >NUL
if %errorlevel% neq 0 (
    echo [!!] Ollama process is NOT running.
    set HEALTHY=NO
) else (
    echo [OK] Ollama Engine is ONLINE.
)

:: 3. Check WSL & Kali
echo [*] Checking WSL (Kali Linux)...
:: Using PowerShell directly to search for the distro name
powershell -Command "if ((wsl -l -v | Out-String) -like '*kali-linux*') { exit 0 } else { exit 1 }"
if %errorlevel% neq 0 (
    echo [!!] Kali Linux distro is NOT detected in WSL.
    set HEALTHY=NO
) else (
    echo [OK] Kali Linux is detected in WSL.
)

echo.
echo --------------------------------------------------------
if "%HEALTHY%"=="YES" color 0A
if "%HEALTHY%"=="YES" echo [RESULT] SYSTEM IS HEALTHY AND READY!
if "%HEALTHY%"=="NO"  color 0C
if "%HEALTHY%"=="NO"  echo [RESULT] SYSTEM HAS ISSUES. PLEASE RUN Master_Installer.bat
echo --------------------------------------------------------
pause
