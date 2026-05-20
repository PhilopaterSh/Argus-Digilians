@echo off
setlocal enabledelayedexpansion
title Argus Security Framework - Universal AI Setup

echo ========================================================
echo        ARGUS AI AGENT - UNIVERSAL SETUP TOOL
echo ========================================================
echo.

:: 1. Check if Python is installed
echo [*] Checking for Python...
python --version >nul 2>&1
if %errorlevel% equ 0 goto :check_ollama_cmd

:: Fallback: Check common installation path
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    echo [OK] Python found in LocalAppData. Prioritizing it in PATH...
    set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    goto :check_ollama_cmd
)

:install_python
echo [!] Python not found. Installing Python 3.12 via Winget...
winget install --id Python.Python.3.12 --source winget --exact --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [ERROR] Automatic Python installation failed. Please install manually.
    exit /b 1
)
echo [SUCCESS] Python installed.
echo [!] PLEASE RESTART YOUR TERMINAL to update the PATH, then run the installer again.
exit /b 1

:check_ollama_cmd
:: 2. Check if Ollama Command Exists
where ollama >nul 2>&1
if errorlevel 1 (
    echo [CRITICAL] Ollama is not installed on this system.
    echo [*] Please install it from https://ollama.com/
    exit /b 1
)

:: 3. Check if Ollama is running
echo [1/4] Verifying Ollama Intelligence Engine...
tasklist /FI "IMAGENAME eq ollama app.exe" 2>NUL | find /I /N "ollama app.exe">NUL
if errorlevel 1 goto :start_ollama
echo [OK] Ollama Engine is running.
goto :select_model

:start_ollama
echo [WARNING] Ollama is NOT running. Attempting to start the engine...
start "" "ollama app.exe"
timeout /t 5 >nul
goto :select_model

:select_model
:: 4. Intelligence Core Selection (Hardcoded)
set "selected_model=WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"

echo.
echo [2/4] Validating Intelligence Model...
echo [INFO] Target: %selected_model%

:: Check Disk Space before pulling (approx 5GB for 7B models)
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "[Math]::Round((Get-PSDrive C).Free / 1GB, 1)"`) do set "FREE_SPACE=%%a"
powershell -Command "if ([float]%FREE_SPACE% -lt 5) { Write-Host '[CRITICAL] Less than 5GB free. Model pull might fail.' -ForegroundColor Red; exit 1 }"
if %errorlevel% neq 0 (
    exit /b 1
)

:pull_loop
:: Check if model exists in 'ollama list'
ollama list | findstr /I "%selected_model%" >nul
if %errorlevel% equ 0 (
    echo [OK] Model is ready for operations.
    goto :setup_venv
)

:download_model
echo [INFO] Model '%selected_model%' not found or incomplete.
echo [*] Starting automated download...
echo [*] This process depends on your internet speed. Please wait.
ollama pull %selected_model%
if %errorlevel% neq 0 (
    echo [!] Download failed. Retrying in 10 seconds...
    timeout /t 10 >nul
    goto :pull_loop
)
echo [SUCCESS] Model pulled successfully.
goto :setup_venv

:setup_venv
:: 5. Setup Virtual Environment (Standardized at Root)
echo.
echo [3/4] Preparing isolated environment (.venv at Root)...
cd /d "%~dp0\.."
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create Virtual Environment.
        exit /b 1
    )
    echo [OK] Created new virtual environment.
) else (
    echo [OK] Using existing virtual environment.
)

:: 6. Install/Update Python Libraries
echo.
echo [4/4] Synchronizing Intelligence Libraries...
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment activation script not found!
    exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
if exist "%~dp0requirements.txt" (
    pip install -r "%~dp0requirements.txt" --quiet
    if errorlevel 1 (
        echo [ERROR] Library synchronization failed.
        exit /b 1
    )
    echo [OK] All libraries are up to date.
) else (
    echo [ERROR] requirements.txt not found at %~dp0requirements.txt!
    exit /b 1
)


echo.
echo ========================================================
echo [SUCCESS] Argus AI Environment is 100%% Operational!
echo [INFO] Active Model: %selected_model%
echo [INFO] Environment: Root .venv
echo ========================================================
if "%ARGUS_AUTO_INSTALL%"=="" pause

