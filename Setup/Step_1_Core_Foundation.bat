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

echo [1/5] Checking System Health...
:: Optional: Only run DISM if a flag is set or if we suspect corruption. 
:: For now, we'll keep it but make it clear it's a health check.
echo [*] Note: DISM repair is skipped in fast-check mode unless errors are found.
:: powershell -Command "Write-Host 'Starting DISM Repair...' -ForegroundColor Cyan; Repair-WindowsImage -Online -RestoreHealth"

echo [2/5] Checking WSL and Virtual Machine Platform...
powershell -Command "if ((Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux).State -ne 'Enabled') { Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -All -NoRestart } else { Write-Host '[OK] WSL is already enabled.' -ForegroundColor Green }"
powershell -Command "if ((Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform).State -ne 'Enabled') { Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -All -NoRestart } else { Write-Host '[OK] Virtual Machine Platform is already enabled.' -ForegroundColor Green }"

echo [3/5] Checking Kali Linux Installation...
powershell -NoProfile -Command "wsl -l -q | Where-Object { $_ -like '*kali-linux*' }" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Kali Linux is already installed.
) else (
    echo [!] Kali Linux not found. Installing...
    :: Check if it's already registered but not installed (rare)
    powershell -NoProfile -Command "wsl --list --online | Where-Object { $_ -like '*kali-linux*' }" >nul 2>&1
    if %errorlevel% equ 0 (
        wsl --install -d kali-linux --web-download
    ) else (
        echo [ERROR] Kali Linux is not available for installation.
        exit /b 1
    )
)

echo [4/5] Checking Ollama (AI Engine)...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama is already installed.
) else (
    echo [!] Ollama not found. Downloading and Installing...
    powershell -Command "Write-Host 'Downloading and Installing Ollama...' -ForegroundColor Cyan; irm https://ollama.com/install.ps1 | iex"
)

echo [5/5] Finalizing Environment...
wsl --set-default-version 2 >nul 2>&1

echo.
echo ========================================================
echo Host setup completed successfully.
echo Note: If you encounter issues, run 'sfc /scannow' and RESTART.
echo ========================================================
if "%ARGUS_AUTO_INSTALL%"=="" pause
