@echo off
setlocal
cd /d "%~dp0"
title Argus Security Framework - Master Installer

:: Redirect to the scripts folder; fall back to PowerShell script if BAT missing
if exist "scripts\INSTALL_EVERYTHING.bat" (
    call scripts\INSTALL_EVERYTHING.bat %*
) else if exist "scripts\INSTALL_EVERYTHING.ps1" (
    powershell -ExecutionPolicy Bypass -File "scripts\INSTALL_EVERYTHING.ps1" %*
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Installation failed with exit code %errorlevel%.
        pause
        exit /b %errorlevel%
    )
) else (
    echo [ERROR] scripts\INSTALL_EVERYTHING.bat or scripts\INSTALL_EVERYTHING.ps1 not found!
    pause
    exit /b 1
)
