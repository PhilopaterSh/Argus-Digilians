@echo off
title Argus AI - Web Studio Launcher

:: Read port from config.yaml
for /f %%p in ('..\..\Argus_venv\Scripts\python.exe ..\..\scripts\get_port.py') do set "PORT=%%p"
echo [*] Starting Argus AI Security Studio on Port %PORT%...

:: Activate Virtual Environment (updated path)
call ..\..\Argus_venv\Scripts\activate.bat
:: Run streamlit from local folder
streamlit run argus_gui.py --server.port %PORT%

pause
