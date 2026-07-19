@echo off
echo Cleaning repository (local artifacts only): desktop.ini, __pycache__, *.pyc
echo Deleting desktop.ini files...
for /r %%f in (desktop.ini) do del /f /q "%%f" 2>nul
echo Removing __pycache__ directories...
for /d /r %%d in (__pycache__) do rd /s /q "%%d" 2>nul
echo Deleting *.pyc files...
for /r %%f in (*.pyc) do del /f /q "%%f" 2>nul
echo Cleanup complete.
pause