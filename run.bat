@echo off
SETLOCAL EnableDelayedExpansion

:: 0. Load Version
if exist "VERSION" (
    set /p APP_VERSION=<VERSION
) else (
    set APP_VERSION=Unknown
)

echo [PLM Organizer Launcher v%APP_VERSION%]
echo ===============================

:: 1. Identify Python Command
if exist "venv\Scripts\python.exe" (
    set PY_CMD=venv\Scripts\python.exe
) else (
    set PY_CMD=python
)

:: 2. Check and Install Dependencies
echo [*] Checking libraries...
%PY_CMD% -c "import PyQt6, flask, watchdog, win32gui" >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [!] Dependencies missing. Installing...
    %PY_CMD% -m pip install -r requirements.txt
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Installation failed.
        pause
        exit /b
    )
)

:: 3. Kill existing instances to avoid port/file locks
echo [*] Cleaning up old processes...
taskkill /f /im pythonw.exe >nul 2>&1

:: 4. Launch App
echo [*] Launching App...
if exist "venv\Scripts\pythonw.exe" (
    set PYW_CMD=venv\Scripts\pythonw.exe
) else (
    set PYW_CMD=pythonw
)

:: Launch detached and exit CMD
start /b "" "%PYW_CMD%" main.py
exit
