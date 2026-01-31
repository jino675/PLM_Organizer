@echo off
SETLOCAL EnableDelayedExpansion

echo [PLM Organizer Launcher v1.3.6]
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
:: We use regular python.exe for now to ensure errors are VISIBLE if it crashes.
:: We can switch back to pythonw once we confirm stability.
%PY_CMD% main.py

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [!] App crashed with error code !ERRORLEVEL!.
    echo.
    pause
)
exit
