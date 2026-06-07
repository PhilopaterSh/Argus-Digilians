@echo off
setlocal enabledelayedexpansion
set "DISTRO_NAME=kali-linux"
set "SCRIPT_WIN=%~dp0check_and_install.sh"

echo ========================================================
echo        ARGUS KALI TOOLS SETUP
echo ========================================================

where wsl >nul 2>&1
if errorlevel 1 (
    echo [ERROR] wsl.exe was not found. Enable WSL and rerun Step 1.
    exit /b 1
)

if not exist "%SCRIPT_WIN%" (
    echo [ERROR] Missing Kali installer script: %SCRIPT_WIN%
    exit /b 1
)

set "DISTRO_FOUND="
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$names = (wsl -l -q 2>$null) -replace \"`0\", ''; if ($names | Where-Object { $_.Trim() -ieq '!DISTRO_NAME!' }) { 'FOUND' }"`) do set "DISTRO_FOUND=%%a"
if /I not "%DISTRO_FOUND%"=="FOUND" (
    echo [ERROR] WSL distribution '%DISTRO_NAME%' is not installed or not functional.
    echo [INFO] Run Step 1 first, reboot if Windows features were enabled, then rerun this installer.
    exit /b 1
)

for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "$p = (Resolve-Path -LiteralPath '%SCRIPT_WIN%').Path; $drive = $p.Substring(0,1).ToLowerInvariant(); $rest = $p.Substring(2).Replace('\','/'); '/mnt/' + $drive + $rest"`) do set "LINUX_PATH=%%a"
if "%LINUX_PATH%"=="" (
    echo [ERROR] Failed to resolve WSL path for: %SCRIPT_WIN%
    exit /b 1
)

echo [INFO] Target distro: %DISTRO_NAME%
echo [INFO] Linux script: %LINUX_PATH%

wsl -s "!DISTRO_NAME!" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Could not set '%DISTRO_NAME%' as the default WSL distribution. Continuing with current default.
)

echo [INFO] Normalizing line endings...
wsl -u root bash -lc "sed -i 's/\r$//' '!LINUX_PATH!'"
if errorlevel 1 (
    echo [ERROR] Failed to normalize line endings inside WSL.
    exit /b 1
)

echo [INFO] Running Kali tool installer...
wsl -u root bash -lc "bash '!LINUX_PATH!'"
if errorlevel 1 (
    echo [ERROR] Kali tool setup failed. Review the console output above.
    exit /b 1
)

echo.
echo [OK] Kali tool setup completed.
if "%ARGUS_AUTO_INSTALL%"=="" pause
