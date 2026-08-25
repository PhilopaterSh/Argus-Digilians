@echo off
REM ===========================================================================
REM  Argus - headless browser screenshot demo (specs/029)
REM ---------------------------------------------------------------------------
REM  Starts a small deliberately-vulnerable web server on 127.0.0.1, lets the
REM  headless browser walk the three capture steps against it, then opens the
REM  folder with the resulting PNGs.
REM
REM  Nothing leaves this machine: no external host is contacted and the file
REM  the traversal leaks is a fixture the script creates in a temp folder.
REM ===========================================================================
setlocal
cd /d "%~dp0.."

echo.
echo  Running the headless browser capture demo...
echo.

"%CD%\Argus_venv\Scripts\python.exe" "tests\manual\verify_browser_poc.py"
set RESULT=%ERRORLEVEL%

echo.
if %RESULT% NEQ 0 (
    echo  [FAILED] The browser could not complete the capture - see the output above.
    echo  If it says Playwright is missing, run:
    echo      Argus_venv\Scripts\python.exe -m pip install playwright
    echo      Argus_venv\Scripts\python.exe -m playwright install chromium
    pause
    exit /b %RESULT%
)

echo  [OK] Screenshots written to artifacts\screenshots
echo  Opening the folder...
start "" "%CD%\artifacts\screenshots"
pause
endlocal
