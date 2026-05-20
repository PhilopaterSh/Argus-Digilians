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

:: 0. Connectivity & Resource Check
echo [*] Verifying System Readiness...

:: Connectivity
powershell -Command "try { $client = New-Object System.Net.WebClient; $client.DownloadString('http://www.google.com') | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% neq 0 (
    powershell -Command "Write-Host '[ERROR] No Internet Connection detected. Please connect and try again.' -ForegroundColor Red"
    pause & exit /b
)
echo [OK] Internet Connection verified.

:: Python & Winget Dependency Check
echo [*] Checking for Python...
python --version >nul 2>&1
if %errorlevel% equ 0 goto :python_ok

:: Fallback: Check common installation path
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    echo [OK] Python found in LocalAppData. Prioritizing it in PATH...
    set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    goto :python_ok
)

echo [!] Python not found. Attempting automated installation...
    
:: Check for Winget
winget --version >nul 2>&1
if !errorlevel! neq 0 (
    powershell -Command "Write-Host '[ERROR] Winget is not recognized. Please install Python 3.12 manually from python.org.' -ForegroundColor Red"
    pause & exit /b
)

:: Try Winget Install
set "PYTHON_SUCCESS=0"
winget install --id Python.Python.3.12 --source winget --exact --silent --accept-package-agreements --accept-source-agreements && set "PYTHON_SUCCESS=1"

if "!PYTHON_SUCCESS!"=="0" (
    echo [!] Winget failed. Attempting to repair Winget sources...
    winget source reset --force
    timeout /t 2 >nul
    winget install --id Python.Python.3.12 --source winget --exact --silent --accept-package-agreements --accept-source-agreements && set "PYTHON_SUCCESS=1"
)

if "!PYTHON_SUCCESS!"=="0" (
    powershell -Command "Write-Host '[ERROR] Python installation failed via Winget. Please install Python 3.12 manually.' -ForegroundColor Red"
    pause & exit /b
)

echo [SUCCESS] Python installed.
:: Disable App Execution Aliases for Python (prevents the 'Microsoft Store' popup)
powershell -Command "Get-AppExecutionAlias | Where-Object { $_.Name -match 'python' } | Disable-AppExecutionAlias" >nul 2>&1

echo [!] PLEASE RESTART this terminal and run the installer again to continue.
pause & exit /b

:python_ok
echo [OK] Python is available.

:: RAM Check (Minimum 8GB recommended for AI models)
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "[Math]::Round((Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize / 1048576)"`) do set "RAM_GB=%%a"
if !RAM_GB! lss 8 (
    powershell -Command "Write-Host '[WARNING] Low RAM detected (!RAM_GB!GB). AI models may perform slowly. 16GB+ recommended.' -ForegroundColor Yellow"
) else (
    echo [OK] RAM: !RAM_GB!GB detected.
)

:: Disk Space Check (Minimum 20GB free for models and tools)
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "[Math]::Round((Get-PSDrive C).Free / 1GB, 1)"`) do set "FREE_SPACE=%%a"
echo [OK] Disk Space: %FREE_SPACE% GB free on C:
powershell -Command "if ([float]%FREE_SPACE% -lt 20) { Write-Host '[WARNING] Low disk space. You might need 20GB+ for large AI models.' -ForegroundColor Yellow }"

echo.
echo ========================================================
echo        📦 INSTALLATION SUMMARY
echo ========================================================
echo  [1] Infrastructure: WSL2, Kali Linux, Ollama Engine
echo  [2] AI Environment: Python Venv, AI Libraries, Model Pull
echo  [3] Security Tools: Nmap, ProjectDiscovery, Recon Engine
echo ========================================================
echo.
timeout /t 5

:: 1. Setup Host & Kali (WSL2)
echo.
echo [1/3] Preparing Host and Kali Linux Foundation...
echo [*] Script: Setup\Step_1_Core_Foundation.bat
call "Setup\Step_1_Core_Foundation.bat"
if !errorlevel! neq 0 (
    powershell -Command "Write-Host '[ERROR] Host/Kali setup failed.' -ForegroundColor Red"
    pause & exit /b
)

:: 2. Setup Python Environment & Models
echo.
echo [2/3] Preparing Python AI Environment and Models...
echo [*] Script: Setup\Step_2_AI_Python_Env.bat
call "Setup\Step_2_AI_Python_Env.bat"
if !errorlevel! neq 0 (
    powershell -Command "Write-Host '[ERROR] Python setup failed.' -ForegroundColor Red"
    pause & exit /b
)

:: 3. Setup Kali Tools
echo.
echo [3/3] Preparing Security Tools inside Kali Linux...
echo [*] Script: Setup\Step_3_Kali_Tools_Setup.bat
:: Ensure SSH is enabled
wsl -d kali-linux -u root bash -c "mkdir -p /run/sshd && /usr/sbin/sshd"
call "Setup\Step_3_Kali_Tools_Setup.bat"
if !errorlevel! neq 0 (
    powershell -Command "Write-Host '[WARNING] Some Kali tools might have failed.' -ForegroundColor Yellow"
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
