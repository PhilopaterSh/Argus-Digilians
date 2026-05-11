@echo off
setlocal enabledelayedexpansion
:: Set working directory to the script's location
cd /d "%~dp0"
title Argus-Digilians Pro Installer (v2.0)
color 0B

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] ERROR: This Master Installer MUST be run as Administrator.
    echo [!] Attempting to elevate...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo        🛡️ ARGUS SECURITY FRAMEWORK - PRO INSTALLER
echo ========================================================
echo.

:: --- PRE-CHECK: GIT ---
echo [*] Checking Prerequisites...
git --version >nul 2>&1
if errorlevel 1 (
    echo [!] Git not found. Installing Git via Winget...
    winget install --id Git.Git -e --source winget --silent --accept-package-agreements
    if errorlevel 1 (
        echo [ERROR] Git installation failed. Please install manually from https://git-scm.com/
        pause & exit /b
    )
    echo [OK] Git installed successfully.
) else (
    echo [OK] Git is already installed.
)

echo.
echo This process will run 3 phases:
echo 1. Host ^& Kali Linux Setup (WSL2 Foundation)
echo 2. Web Tools Configuration (Inside Kali Distro)
echo 3. Python AI Environment Setup (Standardized .venv)
echo.
set /p "start_confirm=Press [ENTER] to start installation or [Q] to quit: "
if /i "%start_confirm%"=="Q" exit /b

:: --- PHASE 1 ---
echo.
echo [>>> PHASE 1: HOST ^& KALI SETUP <<<]
call "How to satup\setup_kali.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Phase 1 failed. Check logs.
    pause & exit /b
)

:: --- PHASE 2 ---
echo.
echo [>>> PHASE 2: WEB TOOLS CONFIGURATION <<<]
call "Tools\run_check.bat"
if %errorlevel% neq 0 (
    echo [WARNING] Phase 2 had some issues, but continuing...
)

:: --- PHASE 3 ---
echo.
echo [>>> PHASE 3: PYTHON AI ENVIRONMENT SETUP <<<]
:: Pointing to the AI setup tool
call "Library_Python_Requirements\Universal_AI_Setup.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Phase 3 failed.
    pause & exit /b
)

echo.
echo ========================================================
echo [SUCCESS] ARGUS-DIGILIANS IS NOW 100%% OPERATIONAL!
echo ========================================================
echo.
echo [INFO] To start the system, run: START_Argus_AI.bat
echo [INFO] Installation log saved (Internal).
pause

