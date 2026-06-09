@echo off
setlocal enabledelayedexpansion
title Argus Security Framework - Universal AI Setup

echo ========================================================
echo        ARGUS AI AGENT - UNIVERSAL SETUP TOOL
echo ========================================================
echo.

:: 1. Check if Python is installed
echo [*] Checking for Python...
where python >nul 2>&1
if not errorlevel 1 (
    python --version >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Python is already installed. Skipping Python installation.
        goto :check_ollama_cmd
    )
    echo [WARNING] python command exists but is not usable. Checking fallback locations...
)

:: Fallback: Check common installation path
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    echo [OK] Python found in LocalAppData. Prioritizing it in PATH...
    set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    goto :check_ollama_cmd
)

:install_python
echo [!] Python not found. Installing Python 3.12 via Winget...
where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Winget is not available. Please install Python 3.12 manually from python.org.
    exit /b 1
)
winget install --id Python.Python.3.12 --source winget --exact --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [ERROR] Automatic Python installation failed. Please install manually.
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python installation completed but python is still not available in PATH.
    echo [INFO] Please restart the terminal or add Python to PATH.
    exit /b 1
)

echo [SUCCESS] Python installed and confirmed available.

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
:: 4. Intelligence Core Selection
if "%ARGUS_MODEL%"=="" (
    set "selected_model=WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"
) else (
    set "selected_model=%ARGUS_MODEL%"
)
if "%ARGUS_MODEL_MIN_GB%"=="" set "ARGUS_MODEL_MIN_GB=8"
if "%ARGUS_MODEL_PULL_RETRIES%"=="" set "ARGUS_MODEL_PULL_RETRIES=3"

echo.
echo [2/4] Validating Intelligence Model...
echo [INFO] Target: %selected_model%
echo [INFO] Override with: set ARGUS_MODEL=model-name

:: Check Disk Space before pulling on the project drive.
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$drive = Split-Path -Qualifier '%~dp0'; $name = $drive.TrimEnd(':'); [Math]::Round((Get-PSDrive $name).Free / 1GB, 1)"`) do set "FREE_SPACE=%%a"
powershell -NoProfile -Command "if ([float]'%FREE_SPACE%' -lt [float]'%ARGUS_MODEL_MIN_GB%') { Write-Host '[CRITICAL] Less than %ARGUS_MODEL_MIN_GB%GB free. Select a smaller model or free disk space.' -ForegroundColor Red; exit 1 }"
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
set /a PULL_ATTEMPT=0

:pull_attempt
set /a PULL_ATTEMPT+=1
echo [INFO] Pull attempt !PULL_ATTEMPT!/%ARGUS_MODEL_PULL_RETRIES%...
ollama pull %selected_model%
if %errorlevel% neq 0 (
    if !PULL_ATTEMPT! geq %ARGUS_MODEL_PULL_RETRIES% (
        echo [ERROR] Model download failed after %ARGUS_MODEL_PULL_RETRIES% attempts.
        exit /b 1
    )
    echo [WARNING] Download failed. Retrying in 10 seconds...
    timeout /t 10 /nobreak >nul
    goto :pull_attempt
)
echo [SUCCESS] Model pulled successfully.
goto :setup_venv

:setup_venv
:: 5. Setup Virtual Environment (Standardized at Root)
echo.
echo [3/4] Preparing isolated environment (Argus_venv at Root)...
cd /d "%~dp0\.."
if not exist "Argus_venv" (
    python -m venv Argus_venv
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
if not exist "Argus_venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment activation script not found!
    exit /b 1
)
call Argus_venv\Scripts\activate.bat

:: Optimized: Only run pip install if requirements.txt is newer than our marker
set "MARKER=Argus_venv\.requirements_installed"
set "REQ=%~dp0requirements.txt"

if exist "%REQ%" (
    set "RUN_PIP=NO"
    if not exist "%MARKER%" (
        set "RUN_PIP=YES"
    ) else (
        for /f "usebackq" %%A in ('%REQ%') do set "REQ_TIME=%%~tA"
        for /f "usebackq" %%A in ('%MARKER%') do set "MARKER_TIME=%%~tA"
        if "!REQ_TIME!" NEQ "!MARKER_TIME!" set "RUN_PIP=YES"
    )

    if "!RUN_PIP!"=="YES" (
        echo [INFO] Updating libraries (this may take a moment)...
        python -m pip install --upgrade pip --quiet
        pip install -r "%REQ%" --quiet
        if %errorlevel% equ 0 (
            echo. > "%MARKER%"
            echo [OK] All libraries are up to date.
        ) else (
            echo [ERROR] Library synchronization failed.
            exit /b 1
        )
    ) else (
        echo [OK] Libraries already satisfied (skip).
    )
) else (
    echo [ERROR] requirements.txt not found at %~dp0requirements.txt!
    exit /b 1
)


echo.
echo ========================================================
echo [SUCCESS] Argus AI Environment is 100%% Operational!
echo [INFO] Active Model: %selected_model%
echo [INFO] Environment: Root Argus_venv
echo ========================================================
if "%ARGUS_AUTO_INSTALL%"=="" pause

