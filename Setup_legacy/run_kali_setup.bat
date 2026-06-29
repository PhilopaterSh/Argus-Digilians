@echo off
set "DISTRO_NAME=kali-linux"

:: Dynamically find the WSL path for the shell script
for /f "usebackq tokens=*" %%a in (`wsl wslpath "%~dp0setup_python_kali.sh"`) do set "LINUX_PATH=%%a"

echo ========================================================
echo     Triggering Python Setup inside %DISTRO_NAME%
echo     Path: %LINUX_PATH%
echo ========================================================

:: Execute the Linux script inside WSL
wsl -d %DISTRO_NAME% -u root bash %LINUX_PATH%

echo.
echo Process finished inside Kali.
pause
