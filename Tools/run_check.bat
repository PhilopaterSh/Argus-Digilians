@echo off
set "DISTRO_NAME=kali-linux"
set "LINUX_PATH=/mnt/c/AI_PenTest_Project/Argus/Tools/check_and_install.sh"

echo Running Linux Tool Check from Windows...
echo Target Distro: %DISTRO_NAME%

:: Execute the shell script inside WSL
wsl -d %DISTRO_NAME% bash %LINUX_PATH%

echo.
echo Process finished.
pause
