@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Argus Security Framework - Master Installer
color 0B

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ERROR: This script MUST be run as Administrator.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo        🛡️ ARGUS SECURITY FRAMEWORK - INSTALLER
echo ========================================================
echo.

:: 1. Setup Host & Kali (WSL2)
echo [1/3] Preparing Host and Kali Linux Foundation...
call "How to satup\setup_kali.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Host/Kali setup failed.
    pause & exit /b
)

:: 2. Setup Python Environment & Models
echo.
echo [2/3] Preparing Python AI Environment and Models...
call "Library_Python_Requirements\Universal_AI_Setup.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Python setup failed.
    pause & exit /b
)

:: 3. Setup Kali Tools
echo.
echo [3/3] Preparing Security Tools inside Kali Linux...
:: Ensure SSH is enabled and tools are installed
wsl -d kali-linux -u root service ssh start
call "Tools\run_check.bat"
if %errorlevel% neq 0 (
    echo [WARNING] Some Kali tools might have failed to install.
)

echo.
echo ========================================================
echo [SUCCESS] Argus Installation is Complete!
echo [INFO] Use 'LAUNCH_STUDIO.bat' to start the system.
echo ========================================================
pause
