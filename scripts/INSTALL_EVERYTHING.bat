@echo off
setlocal
cd /d "%~dp0"
title Argus Security Framework - Master Installer

echo ========================================================
echo        ARGUS SECURITY FRAMEWORK - INSTALLER
echo ========================================================
echo.

:: Check for PowerShell
where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell is required but not found in PATH.
    pause
    exit /b 1
)

:: Run the PowerShell Installer
powershell -ExecutionPolicy Bypass -File "INSTALL_EVERYTHING.ps1" %*

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed with exit code %errorlevel%.
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Installation process completed.
pause
