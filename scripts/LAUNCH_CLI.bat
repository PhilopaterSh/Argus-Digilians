@echo off
setlocal enabledelayedexpansion

:: --- ARGUS CLI LAUNCHER ---
:: This script activates the environment and runs the Argus Intelligence CLI.

title Argus AI - Intelligence CLI
cls

:: 0. Always run from the project root, regardless of the caller's own
::    working directory (a plain double-click in Explorer starts in this
::    script's own scripts\ folder, not the root - every check/path below
::    is written relative to the root, matching TEST_ARGUS.bat's existing
::    pattern). Real bug, confirmed live: without this, "Argus_venv\" below
::    resolved to the non-existent scripts\Argus_venv\ and failed even
::    though the real Argus_venv\ existed one level up.
cd /d "%~dp0.."

:: 1. Environment Check
if not exist "Argus_venv\" (
    echo [!] Virtual environment not found. Run INSTALL.bat from the project root first.
    pause
    exit /b 1
)

:: 2. Activate Venv
call Argus_venv\Scripts\activate.bat

:: 3. Ask for a target if none was passed on the command line (e.g. a plain
::    double-click) - without this, run_argus_cli.py silently falls back to
::    its own hardcoded default target, which is confusing for anyone who
::    didn't already know that from reading the Python source.
set "TARGET=%~1"
if "%TARGET%"=="" (
    set /p TARGET="Enter the target URL to scan (e.g. https://example.com): "
)
if "%TARGET%"=="" (
    echo [!] No target entered. Exiting.
    pause
    exit /b 1
)

:: 4. Run CLI Analysis
echo [!] Starting Argus Autonomous Agent against: %TARGET%
python scripts/run_argus_cli.py "%TARGET%"

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
