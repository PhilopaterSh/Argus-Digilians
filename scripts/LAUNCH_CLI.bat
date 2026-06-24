@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."

:: --- ARGUS CLI LAUNCHER ---
:: This script activates the environment and runs the Argus Intelligence CLI.

title Argus AI - Intelligence CLI
cls

:: 1. Environment Check
if not exist "Argus_venv\" (
    echo [!] Virtual environment not found. Running setup...
    call scripts\INSTALL_EVERYTHING.bat
)

:: 2. Activate Venv
call Argus_venv\Scripts\activate.bat

:: 3. Resolve target: accept as CLI arg or prompt interactively (like LAUNCH_STUDIO)
set "TARGET=%~1"
if "%TARGET%"=="" (
    echo.
    set /p TARGET="Enter target URL (or press Enter for default https://example.com): "
    if "%TARGET%"=="" set "TARGET=https://example.com/"
)

:: 4. Run CLI Analysis
echo [!] Starting Argus Autonomous Agent...
echo [*] Target: %TARGET%
python run_argus_cli.py %TARGET%

:: 5. Keep window open if error or finished
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Argus stopped with an error code: %ERRORLEVEL%
    pause
) else (
    echo.
    echo [*] Analysis Session Completed Successfully.
    pause
)
