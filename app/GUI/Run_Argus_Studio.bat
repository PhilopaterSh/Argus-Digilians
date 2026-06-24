@echo off
title Argus AI - Web Studio Launcher
echo [*] Starting Argus AI Security Studio on Port 12189...
echo [*] Please wait while the environment initializes...

:: Activate Virtual Environment (updated path)
call ..\..\Argus_venv\Scripts\activate.bat
:: Run streamlit from local folder
streamlit run argus_gui.py --server.port 12189

pause
