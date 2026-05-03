@echo off
setlocal enabledelayedexpansion
title Argus-Digilians Master Installer

:: Check for Administrator privileges
echo Testing for Admin Privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] This Master Installer MUST be run as Administrator.
    echo [!] Attempting to elevate...
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo        ARGUS-DIGILIANS COMPLETE MASTER SETUP
echo ========================================================
echo.
echo This process will run 3 phases:
echo 1. Host ^& Kali Linux Setup
echo 2. Web Tools Configuration (Inside Kali)
echo 3. Python AI Environment Setup (Universal)
echo.
pause

echo.
echo [>>> PHASE 1: HOST ^& KALI SETUP <<<]
call "How to satup\setup_kali.bat"

echo.
echo [>>> PHASE 2: WEB TOOLS CONFIGURATION <<<]
call "Tools\run_check.bat"

echo.
echo [>>> PHASE 3: PYTHON AI ENVIRONMENT SETUP <<<]
call "Library_Python_Requirements\Universal_AI_Setup.bat"

echo.
echo ========================================================
echo        ALL SETUP PHASES COMPLETED SUCCESSFULLY!
echo ========================================================
echo You are now ready to use Argus-Digilians.
pause
