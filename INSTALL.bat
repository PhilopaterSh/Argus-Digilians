@echo off
REM ==========================================================================
REM  Argus Security Framework - Single-Click Master Installer (Launcher)
REM --------------------------------------------------------------------------
REM  This launcher runs scripts\ARGUS_INSTALLER.ps1, which will:
REM    * self-elevate to Administrator
REM    * install + configure + validate the entire Argus environment
REM    * write a log to logs\argus_install_<timestamp>.log
REM
REM  Usage:
REM    Double-click this file, or from a terminal:
REM        INSTALL.bat              (full install, auto-elevates)
REM        INSTALL.bat dryrun       (simulate; no system changes)
REM        INSTALL.bat offline      (skip all network downloads)
REM        INSTALL.bat interactive  (confirm before each step)
REM
REM  Optional ARG_* tokens below are forwarded as -ArgumentList to PowerShell.
REM ==========================================================================
setlocal enabledelayedexpansion
title Argus Security Framework - Installer
color 0B

cd /d "%~dp0"

echo ========================================================
echo          ARGUS SECURITY FRAMEWORK - INSTALLER
echo ========================================================
echo.

set "PS1=scripts\ARGUS_INSTALLER.ps1"

if not exist "%PS1%" (
    echo [ERROR] Master installer not found: %PS1%
    echo [INFO]  Make sure you are running this from the project root.
    echo.
    pause
    exit /b 1
)

REM Forward the first argument as an installer mode, if recognized.
set "ARG="
if /I "%~1"=="dryrun"      set "ARG=-DryRun"
if /I "%~1"=="offline"     set "ARG=-Offline"
if /I "%~1"=="interactive" set "ARG=-Interactive"
if /I "%~1"=="skiphealth"  set "ARG=-SkipHealthCheck"

echo [INFO] Launching PowerShell master installer...
if defined ARG (
    echo [INFO] Mode: %ARG%
)
echo [INFO] A UAC prompt may appear - please accept to grant Admin rights.
echo.

REM -NoProfile avoids profile-load delays; -ExecutionPolicy Bypass allows the
REM script to run in this scope without changing the machine policy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %ARG%

set "RC=%ERRORLEVEL%"
echo.
echo ========================================================
if "%RC%"=="0" (
    echo  [DONE] Installation finished successfully.
    echo  Use scripts\LAUNCH_STUDIO.bat to start the system.
) else (
    echo  [EXIT] Installer exited with code %RC%.
    echo  Review the log in the logs\ folder for details.
)
echo ========================================================
echo.
pause
endlocal
exit /b %RC%
