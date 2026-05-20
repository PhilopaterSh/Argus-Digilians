@echo off
set "DISTRO_NAME=kali-linux"

:: Dynamically find the WSL path for the shell script
for /f "usebackq tokens=*" %%a in (`wsl wslpath "%~dp0check_and_install.sh"`) do set "LINUX_PATH=%%a"

echo Running Linux Tool Check from Windows...
echo Target Distro: %DISTRO_NAME%
echo Linux Script Path: %LINUX_PATH%

:: Self-healing: Ensure Unix line endings before execution
wsl -d %DISTRO_NAME% -u root sed -i 's/\r$//' %LINUX_PATH%

:: Execute the shell script inside WSL as root to avoid sudo prompts
wsl -d %DISTRO_NAME% -u root bash %LINUX_PATH%

echo.
echo Process finished.
if "%ARGUS_AUTO_INSTALL%"=="" pause
