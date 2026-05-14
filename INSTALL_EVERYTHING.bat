@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Argus Security Framework - Master Installer
color 0B
set ARGUS_AUTO_INSTALL=1
set LOG_FILE=ARGUS_INSTALLATION.log

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ERROR: This script MUST be run as Administrator.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: Initialize Log
echo [%date% %time%] --- Starting Argus Installation --- > "%LOG_FILE%"

echo ========================================================
echo        🛡️ ARGUS SECURITY FRAMEWORK - INSTALLER
echo ========================================================
echo.

:: 0. Connectivity Check
echo [*] Verifying Internet Connection...
powershell -Command "try { $client = New-Object System.Net.WebClient; $client.DownloadString('http://www.google.com') | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '[ERROR] No Internet Connection detected. Please connect and try again.' -ForegroundColor Red"
    pause & exit /b
)
echo [OK] Connection verified.

:: 1. Setup Host & Kali (WSL2)
echo.
echo [1/3] Preparing Host and Kali Linux Foundation...
echo [*] Log: 01_Infrastructure_Setup\Step_1_Core_Foundation.bat
call "01_Infrastructure_Setup\Step_1_Core_Foundation.bat" >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '[ERROR] Host/Kali setup failed. Check %LOG_FILE% for details.' -ForegroundColor Red"
    pause & exit /b
)

:: 2. Setup Python Environment & Models
echo.
echo [2/3] Preparing Python AI Environment and Models...
echo [*] Log: 02_AI_Environment\Step_2_AI_Python_Env.bat
call "02_AI_Environment\Step_2_AI_Python_Env.bat" >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '[ERROR] Python setup failed. Check %LOG_FILE% for details.' -ForegroundColor Red"
    pause & exit /b
)

:: 3. Setup Kali Tools
echo.
echo [3/3] Preparing Security Tools inside Kali Linux...
echo [*] Log: Tools\Step_3_Kali_Tools_Setup.bat
:: Ensure SSH is enabled and tools are installed
wsl -d kali-linux -u root service ssh start >> "%LOG_FILE%" 2>&1
call "Tools\Step_3_Kali_Tools_Setup.bat" >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '[WARNING] Some Kali tools might have failed. Check %LOG_FILE%.' -ForegroundColor Yellow"
)

echo.
echo ========================================================
echo        🚀 RUNNING SYSTEM FINAL VALIDATION
echo ========================================================
:: Run Health Check in "Auto" mode (we will modify it to support this)
set ARGUS_SKIP_PAUSE=1
call "CHECK_HEALTH.bat"

echo.
echo ========================================================
echo [SUCCESS] Argus Installation Process Finished!
echo [INFO] A detailed log is available at: %LOG_FILE%
echo [INFO] Use 'LAUNCH_STUDIO.bat' to start the system.
echo ========================================================
pause
