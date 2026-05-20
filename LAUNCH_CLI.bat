@echo off
setlocal enabledelayedexpansion

:: --- ARGUS CLI LAUNCHER ---
:: This script activates the environment and runs the Argus Intelligence CLI.

title Argus AI - Intelligence CLI
cls

:: 1. Environment Check
if not exist "venv\" (
    echo [!] Virtual environment not found. Running setup...
    call INSTALL_EVERYTHING.bat
)

:: 2. Activate Venv
call venv\Scripts\activate.bat

:: 3. Run CLI Analysis
echo [!] Starting Argus Autonomous Agent...
python run_argus_cli.py %*

:: 4. Keep window open if error or finished
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Argus stopped with an error code: %ERRORLEVEL%
    pause
) else (
    echo.
    echo [*] Analysis Session Completed Successfully.
    pause
)
