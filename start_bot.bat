@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found: .venv
    echo Please create it first:
    echo py -m venv .venv
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [ERROR] config.json not found.
    pause
    exit /b 1
)

echo Starting Inazuma Semi AFK...
".venv\Scripts\python.exe" "main.py"

echo.
echo Bot stopped.
pause
