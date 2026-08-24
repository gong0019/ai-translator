@echo off
setlocal
cd /d "%~dp0"

:: 优先检测虚拟环境中的 Python
if exist ".venv\Scripts\python.exe" (
    set "PY_EXEC=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PY_EXEC=venv\Scripts\python.exe"
) else (
    set "PY_EXEC=python"
)

"%PY_EXEC%" translator_cli.py %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Translation program exited with code %ERRORLEVEL%.
    pause
)
