@echo off
SETLOCAL EnableDelayedExpansion

echo [PLM Organizer Launcher]

:: 1. Decide whether to use Virtual Environment or System Python
if exist "venv\Scripts\python.exe" (
    set PY_CMD=venv\Scripts\python.exe
    set PYW_CMD=venv\Scripts\pythonw.exe
) else (
    set PY_CMD=python
    set PYW_CMD=pythonw
)

:: 2. Check if required libraries are already installed (to skip installation)
echo Checking for required libraries...
%PY_CMD% -c "import PyQt6, flask, watchdog, win32gui" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo [OK] Dependencies already met. Launching app...
    :: Launch with pythonw (no console) but if it crashes immediately, help user debug
    start "" !PYW_CMD! main.py
    
    :: Give it a second to see if it stays alive
    timeout /t 2 >nul
    tasklist /fi "imagename eq pythonw.exe" | find ":" >nul
    if !ERRORLEVEL! NEQ 0 (
        exit
    ) else (
        echo [!] App may have crashed on startup. Try running main.py manually to see error.
        pause
        exit
    )
)

:: 3. If libraries are missing, attempt installation
echo [INFO] Dependencies missing. Starting setup...

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create venv. Using system Python instead.
        set PY_CMD=python
        set PYW_CMD=pythonw
    ) else (
        set PY_CMD=venv\Scripts\python.exe
        set PYW_CMD=venv\Scripts\pythonw.exe
    )
)

echo [INFO] Installing required libraries...
echo (If this gets stuck, your company network might be blocking PyPI.)
%PY_CMD% -m pip install -r requirements.txt --no-cache-dir

if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [ERROR] Installation failed or timed out.
    echo.
    echo Possible reasons:
    echo 1. Corporate Firewall/Proxy blocking 'pip'
    echo 2. No internet access
    echo.
    echo Try running: pip install PyQt6 flask watchdog --user
    echo manually in your CMD.
    pause
    exit /b
)

echo Starting PLM Organizer...
start "" !PYW_CMD! main.py

:: Small delay to check if it crashed immediately
timeout /t 2 >nul
tasklist /fi "imagename eq pythonw.exe" | find "pythonw.exe" >nul
if !ERRORLEVEL! EQU 0 (
    echo [OK] App launched successfully.
    exit
) else (
    echo.
    echo [!] App may have failed to start silently.
    echo.
    echo To see what's wrong, please run this manually:
    echo     %PY_CMD% main.py
    echo.
    pause
)
exit
