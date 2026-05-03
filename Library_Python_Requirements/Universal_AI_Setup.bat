@echo off
setlocal enabledelayedexpansion
title Universal AI Agent Setup Tool

echo ========================================================
echo        AI AGENT ZERO-TOUCH INSTALLER (WINDOWS)
echo ========================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found. Starting Silent Installation via Winget...
    echo [*] This may take a few minutes. Please wait...
    
    :: Use winget to install Python 3.12 silently
    winget install --id Python.Python.3.12 --exact --silent --accept-package-agreements --accept-source-agreements
    
    if !errorlevel! neq 0 (
        echo [✗] Winget failed. Please install Python manually from python.org
        pause
        exit /b
    )
    
    echo [✓] Python installed successfully. Refreshing environment...
    :: Refresh Path for the current session
    refreshenv >nul 2>&1 || (
        set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python312\;%LocalAppData%\Programs\Python\Python312\Scripts\"
    )
) else (
    for /f "tokens=2" %%v in ('python --version') do echo [✓] Python already present: %%v
)

:: 2. Create Virtual Environment
if not exist ".venv" (
    echo [*] Creating isolated Virtual Environment (.venv)...
    python -m venv .venv
) else (
    echo [✓] Virtual Environment already exists.
)

:: 3. Install Requirements
echo [*] Activating environment and installing libraries...
call .venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip --quiet

if exist "requirements.txt" (
    echo [*] Installing libraries from requirements.txt...
    echo [*] This part includes heavy AI libraries (Torch, FAISS)...
    pip install -r requirements.txt
) else (
    echo [!] Warning: requirements.txt not found. Skipping library install.
)

echo.
echo ========================================================
echo [SUCCESS] Your AI Environment is 100%% Ready!
echo [INFO] To start your agent, run: call .venv\Scripts\activate.bat
echo ========================================================
pause
