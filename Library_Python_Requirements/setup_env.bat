@echo off
setlocal enabledelayedexpansion
title Python Environment Setup & Verification

echo ========================================================
echo        Python Environment Verification ^& Setup
echo ========================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Error: Python is not installed or not in your PATH.
    echo [*] Opening Python download page for you...
    start https://www.python.org/downloads/
    echo.
    echo Please install Python 3.12 or higher, then run this script again.
    pause
    exit /b
)

:: 2. Check Version using a simple PowerShell one-liner for precision
echo Checking Python version...
for /f "tokens=2" %%v in ('python --version') do set "PY_VER=%%v"
echo [+] Found Python version: %PY_VER%

powershell -Command "$v = [version]'%PY_VER%'; if ($v -lt [version]'3.12') { Write-Host '[!] Warning: Python 3.12+ is recommended for best AI performance.' -ForegroundColor Yellow }"

:: 3. Ask for confirmation to install requirements
echo.
set /p "CONFIRM=Do you want to install/update the required Python libraries? (Y/N): "

if /i "%CONFIRM%" neq "Y" (
    echo [!] Setup cancelled by user.
    pause
    exit /b
)

echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo [*] Installing requirements from requirements.txt...
python -m pip install -r "%~dp0requirements.txt"

if %errorlevel% eq 0 (
    echo.
    echo ========================================================
    echo [OK] All Python libraries installed successfully!
    echo ========================================================
) else (
    echo.
    echo [!] Some errors occurred during installation. 
    echo Please check your internet connection.
)

pause
