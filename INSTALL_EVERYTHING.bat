@echo off
setlocal
cd /d "%~dp0"
title Argus Security Framework - Master Installer

:: Redirect to the scripts folder
if exist "scripts\INSTALL_EVERYTHING.bat" (
    call scripts\INSTALL_EVERYTHING.bat %*
) else (
    echo [ERROR] scripts\INSTALL_EVERYTHING.bat not found!
    pause
    exit /b 1
)
