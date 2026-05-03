@echo off
:: Emergency Setup for Kali WSL
:: This version uses PowerShell Direct to bypass DISM/Network issues

echo Testing for Admin Privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] This script MUST be run as Administrator.
    echo [!] Attempting to elevate...
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo        Kali Linux WSL - Emergency Repair ^& Setup
echo ========================================================

echo [1/4] Fixing System Corruption (This may take 5-10 mins)...
powershell -Command "Write-Host 'Starting DISM Repair...' -ForegroundColor Cyan; Repair-WindowsImage -Online -RestoreHealth"

echo [2/4] Enabling WSL and Virtual Machine Platform...
powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -All -NoRestart"
powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart"

echo [3/4] Installing WSL Kernel ^& Kali Linux...
echo (Downloading directly from Microsoft - Bypass Error 12006)
wsl --install -d kali-linux --web-download

echo [4/4] Finalizing...
wsl --set-default-version 2

echo.
echo ========================================================
echo If you see 'The component store has been corrupted', 
echo please run: 'sfc /scannow' and RESTART your computer.
echo ========================================================
pause
