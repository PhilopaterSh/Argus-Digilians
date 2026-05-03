@echo off
set "DISTRO_NAME=kali-linux"
set "LINUX_PATH=/mnt/c/AI_PenTest_Project/Argus/Library_Python_Requirements/setup_python_kali.sh"

echo ========================================================
echo     Triggering Python Setup inside %DISTRO_NAME%
echo ========================================================

:: Execute the Linux script inside WSL
wsl -d %DISTRO_NAME% -u root bash %LINUX_PATH%

echo.
echo Process finished inside Kali.
pause
