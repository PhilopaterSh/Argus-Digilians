@echo off
:: Argus Security Framework - Host ^& AI Foundation Setup
:: This version handles WSL 2, Kali Linux, and Ollama installation.

echo Testing for Admin Privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] This script MUST be run as Administrator.
    echo [!] Attempting to elevate...
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo        ARGUS SECURITY FRAMEWORK - HOST SETUP
echo ========================================================

echo [1/5] Fixing System Corruption (This may take 5-10 mins)...
powershell -Command "Write-Host 'Starting DISM Repair...' -ForegroundColor Cyan; Repair-WindowsImage -Online -RestoreHealth"

echo [2/5] Enabling WSL and Virtual Machine Platform...
powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -All -NoRestart"
powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart"

echo [3/5] Installing WSL Kernel ^& Kali Linux...
echo (Downloading directly from Microsoft - Bypass Error 12006)
wsl --install -d kali-linux --web-download

echo [4/5] Installing Ollama (AI Engine)...
powershell -Command "Write-Host 'Downloading and Installing Ollama...' -ForegroundColor Cyan; irm https://ollama.com/install.ps1 | iex"

echo [5/5] Finalizing Environment...
wsl --set-default-version 2

echo.
echo ========================================================
echo Host setup completed successfully.
echo Note: If you encounter issues, run 'sfc /scannow' and RESTART.
echo ========================================================
if "%ARGUS_AUTO_INSTALL%"=="" pause
