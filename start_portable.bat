@echo off
cd /d "%~dp0"

if not exist "portable_runtime\python\python.exe" (
    echo [ERROR] 找不到 portable_runtime\python\python.exe
    echo 請先執行 build_portable_runtime.ps1 建立可攜式執行環境。
    pause
    exit /b 1
)

set "PYTHONHOME=%~dp0portable_runtime\python"
set "PYTHONPATH=%~dp0portable_runtime\python\Lib;%~dp0portable_runtime\python\Lib\site-packages"

echo 啟動可攜式半自動掛機程式...
"portable_runtime\python\python.exe" "main.py"

echo.
echo 程式已結束。
pause
