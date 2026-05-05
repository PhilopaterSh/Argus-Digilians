@echo off
title Argus AI - Professional Launcher
echo ---------------------------------------------------
echo    🛡️ ARGUS AI SECURITY STUDIO - LAUNCHER
echo ---------------------------------------------------
echo.

:: Check for virtual environment (updated path)
if not exist "..\Library_Python_Requirements\.venv" (
    echo [ERROR] Virtual Environment not found! Run Master_Installer first.
    pause
    exit
)

:: Set Port
set PORT=12189

echo [*] Activating environment...
:: Updated path to activate.bat
call ..\Library_Python_Requirements\.venv\Scripts\activate.bat

echo [*] Starting Studio on http://localhost:%PORT%
echo [*] Press Ctrl+C to stop.
echo.

:: Run Streamlit from the app.py (local to this folder now)
streamlit run app.py --server.port %PORT% --server.headless true

pause
