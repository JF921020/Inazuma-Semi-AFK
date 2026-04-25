@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found: .venv
    echo Please create it first:
    echo py -m venv .venv
    pause
    exit /b 1
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"

if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found.
    pause
    exit /b 1
)

echo Checking required packages...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install required packages.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [ERROR] config.json not found.
    pause
    exit /b 1
)

echo Starting Inazuma Semi AFK...
python "main.py"

echo.
echo Bot stopped.
pause
