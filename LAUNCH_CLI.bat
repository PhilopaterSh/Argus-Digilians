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

set /p TARGET="Enter target URL (default https://example.com): "
if "%TARGET%"=="" set "TARGET=https://example.com"

set /p MODE="Enter mode passive/aggressive (default passive): "
if "%MODE%"=="" set "MODE=passive"

python run_argus_cli.py --target "%TARGET%" --mode "%MODE%"

pause
