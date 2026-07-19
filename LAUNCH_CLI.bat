@echo off
setlocal
cd /d "%~dp0"
title Argus Security Framework - CLI
color 0B

echo ========================================================
echo        ARGUS SECURITY FRAMEWORK - CLI
echo ========================================================
echo.
echo Usage examples:
echo   python run_argus_cli.py --target https://example.com --mode passive
echo   python run_argus_cli.py --dry-run
echo.

set "PYTHONPATH=%~dp0;%PYTHONPATH%"

:: Detect a working Python interpreter (see note in LAUNCH_STUDIO.bat).
set "PYEXE="
where py    >nul 2>&1 && set "PYEXE=py"
if not defined PYEXE ( where python >nul 2>&1 && set "PYEXE=python" )
if not defined PYEXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)
if not defined PYEXE (
    echo [!] Python not found. Install Python 3 from https://www.python.org/downloads/
    echo     and tick "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

set /p TARGET="Enter target URL (default https://example.com): "
if "%TARGET%"=="" set "TARGET=https://example.com"

set /p MODE="Enter mode passive/aggressive (default passive): "
if "%MODE%"=="" set "MODE=passive"

"%PYEXE%" run_argus_cli.py --target "%TARGET%" --mode "%MODE%"

pause
