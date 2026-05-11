@echo off
title Argus Security Framework - Docker Deployer
color 0B
echo ========================================================
echo        🛡️ ARGUS DOCKER DEPLOYMENT SYSTEM
echo ========================================================
echo.

:: 1. Check for Docker
where docker >nul 2>&1
if errorlevel 1 (
    echo [!] Docker is NOT installed.
    echo [*] Attempting to install Docker Desktop via Winget...
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Automated installation failed. Please install Docker Desktop manually.
        pause & exit
    )
    echo [SUCCESS] Docker installed. Please RESTART your PC and run this again.
    pause & exit
)

:: 2. Check if Docker is running
echo [*] Verifying Docker Engine status...
docker info >nul 2>&1
if errorlevel 1 (
    echo [!] Docker is installed but NOT running.
    echo [*] Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo [*] Waiting for Docker to initialize (this may take a minute)...
    timeout /t 30 >nul
)

:: 3. Build and Launch
echo.
echo [*] Deploying Argus Multi-Container Stack...
docker compose up -d --build

echo.
echo ========================================================
echo [SUCCESS] Argus Studio is DEPLOYED!
echo [INFO] Web Interface: http://localhost:12189
echo [INFO] Ollama Status: http://localhost:11434
echo [INFO] Kali-Core: argus-kali-core ^(internal SSH on port 22^)
echo ========================================================
echo.
echo To stop the system, run: docker compose down
echo.
pause
