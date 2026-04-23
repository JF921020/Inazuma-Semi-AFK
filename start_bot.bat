@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] 找不到虛擬環境 .venv
    echo 請先執行虛擬環境建立與套件安裝流程。
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [INFO] 找不到 config.json，先從範例建立一份...
    copy /Y "config.example.json" "config.json" >nul
)

echo 啟動半自動掛機程式...
".venv\Scripts\python.exe" "main.py"

echo.
echo 程式已結束。
pause
