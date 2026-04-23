@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] 找不到虛擬環境 .venv
    echo 請先執行虛擬環境建立與套件安裝流程。
    pause
    exit /b 1
)

echo 啟動截圖取樣工具...
".venv\Scripts\python.exe" "capture_tool.py"

echo.
echo 工具已結束。
pause
