@echo off
title CareFlow Server
echo ========================================================
echo   CareFlow - Multi-Agent Clinical Orchestration System
echo ========================================================
echo.

cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at backend\venv!
    echo Please create it using: py -3.11 -m venv venv
    pause
    exit /b 1
)

echo Activating Python virtual environment...
call venv\Scripts\activate.bat

echo.
echo Launching frontend dashboard in default browser...
start "" "%~dp0frontend\index.html"

echo.
echo ========================================================
echo   CareFlow backend is STARTING on http://127.0.0.1:8000
echo   IMPORTANT: Keep this command window OPEN!
echo   Do NOT press Ctrl+C unless you want to stop the server.
echo ========================================================
echo.

python -m uvicorn main:app --port 8000

pause
