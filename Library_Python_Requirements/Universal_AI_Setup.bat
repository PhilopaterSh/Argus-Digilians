@echo off
setlocal enabledelayedexpansion
title Argus Security Framework - Universal AI Setup

echo ========================================================
echo        ARGUS AI AGENT - UNIVERSAL SETUP TOOL
echo ========================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 goto :install_python
echo [OK] Python is installed.
goto :check_ollama_cmd

:install_python
echo [!] Python not found. Installing Python 3.12 via Winget...
winget install --id Python.Python.3.12 --exact --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [ERROR] Automatic Python installation failed. Please install manually.
    pause & exit /b
)
echo [SUCCESS] Python installed. Please restart this script.
pause & exit /b

:check_ollama_cmd
:: 2. Check if Ollama Command Exists
where ollama >nul 2>&1
if errorlevel 1 (
    echo [CRITICAL] Ollama is not installed on this system.
    echo [*] Please install it from https://ollama.com/
    pause & exit /b
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
set "selected_model=WhiteRabbitNeo/WhiteRabbitNeo-V3-7B"

echo.
echo [2/4] Validating Intelligence Model...
echo [INFO] Target: %selected_model%

:pull_loop
:: Check if model exists in 'ollama list'
ollama list | findstr /I "%selected_model%" >nul
if errorlevel 1 goto :download_model
echo [OK] Model is ready for operations.
goto :setup_venv

:download_model
echo [INFO] Model '%selected_model%' not found or incomplete.
echo [*] Starting automated download (This may take time)...
ollama pull %selected_model%
if errorlevel 1 (
    echo [!] Download failed. Retrying in 5 seconds...
    timeout /t 5 >nul
    goto :pull_loop
)
goto :pull_loop

:setup_venv
:: 5. Setup Virtual Environment (Standardized at Root)
echo.
echo [3/4] Preparing isolated environment (.venv at Root)...
cd /d "%~dp0\.."
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create Virtual Environment.
        pause & exit /b 1
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
    pause & exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
if exist "Library_Python_Requirements\requirements.txt" (
    pip install -r Library_Python_Requirements\requirements.txt --quiet
    if errorlevel 1 (
        echo [ERROR] Library synchronization failed.
        pause & exit /b 1
    )
    echo [OK] All libraries are up to date.
) else (
    echo [ERROR] requirements.txt not found!
    pause & exit /b 1
)

echo.
echo ========================================================
echo [SUCCESS] Argus AI Environment is 100%% Operational!
echo [INFO] Active Model: %selected_model%
echo [INFO] Environment: Root .venv
echo ========================================================
pause

