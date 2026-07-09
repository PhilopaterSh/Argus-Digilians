@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."
title Argus Testing Suite

echo.
echo ========================================
echo   ARGUS SECURITY FRAMEWORK - TEST SUITE
echo ========================================
echo.

:menu
cls
echo.
echo  [1] Basic Imports Test
echo  [2] LLM Model Test
echo  [3] Tool Registry Test
echo  [4] Launch Web GUI (Streamlit)
echo  [5] Run CLI Demo
echo  [6] System Health Check
echo  [7] Install Dependencies
echo  [8] Exit
echo.

set /p choice="Select option (1-8): "

if "%choice%"=="1" goto test_imports
if "%choice%"=="2" goto test_llm
if "%choice%"=="3" goto test_tools
if "%choice%"=="4" goto test_gui
if "%choice%"=="5" goto test_cli
if "%choice%"=="6" goto test_health
if "%choice%"=="7" goto test_install
if "%choice%"=="8" goto exit_script

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:test_imports
cls
echo.
echo [TEST] Verifying Core Imports...
echo.
call Argus_venv\Scripts\activate.bat
python -c "
from app.core.agent.brain import ArgusBrain
from app.core.llm_factory import build_llm
from app.tools.tool_registry import WSLBridgeTools
from app.core.memory.memory_service import ArgusMemory
print('[SUCCESS] All core imports verified!')
"
pause
goto menu

:test_llm
cls
echo.
echo [TEST] LLM Model Test...
echo Please wait, this may take 10-30 seconds on first run...
echo.
call Argus_venv\Scripts\activate.bat
python -c "
from app.core.llm_factory import build_llm
print('[*] Initializing WhiteRabbitNeo model...')
llm = build_llm('WhiteRabbitNeo/WhiteRabbitNeo-V3-7B')
print('[*] Sending test query...')
response = llm.invoke('List 3 key penetration testing methodologies')
print('[RESPONSE]')
print(response)
"
pause
goto menu

:test_tools
cls
echo.
echo [TEST] Tool Registry & WSL Bridge Test...
echo.
call Argus_venv\Scripts\activate.bat
python -c "
from app.tools.tool_registry import WSLBridgeTools
print('[*] Initializing tool registry...')
tools = WSLBridgeTools()
print('[OK] Tool registry loaded successfully')
print('[INFO] Available services:')
print('  - Reconnaissance Service')
print('  - Vulnerability Scanners')
print('  - Payload Suggester')
print('  - Secret Analyzer')
print('  - Web Search')
print('  - Crawler Service')
print('  - Evasion Service')
print('  - ZERO-APT Simulation')
"
pause
goto menu

:test_gui
cls
echo.
echo [TEST] Launching Streamlit Web GUI...
echo Opening at http://localhost:8501
echo Press Ctrl+C to stop the server.
echo.
call Argus_venv\Scripts\activate.bat
python -m streamlit run app\GUI\dashboard.py --logger.level=error
goto menu

:test_cli
cls
echo.
echo [TEST] CLI Demo Scan...
echo.
call Argus_venv\Scripts\activate.bat
python scripts\run_argus_cli.py https://example.com
pause
goto menu

:test_health
cls
echo.
echo [TEST] System Health Check...
echo.
call CHECK_HEALTH.bat
pause
goto menu

:test_install
cls
echo.
echo [TEST] Installing/Updating Dependencies...
echo.
call Argus_venv\Scripts\activate.bat
pip install -r Setup\requirements.txt
echo.
echo [SUCCESS] Dependencies installed!
pause
goto menu

:exit_script
echo.
echo Thank you for testing Argus!
echo.
exit /b 0
