@echo off
SETLOCAL EnableDelayedExpansion

echo [PLM Organizer Launcher]

:: 1. 가상환경 또는 시스템 파이썬 중 무엇을 쓸지 결정
if exist "venv\Scripts\python.exe" (
    set PY_CMD=venv\Scripts\python.exe
    set PYW_CMD=venv\Scripts\pythonw.exe
) else (
    set PY_CMD=python
    set PYW_CMD=pythonw
)

:: 2. 일단 앱에 필요한 라이브러리가 있는지 확인 (설치 단계를 건너뛰기 위함)
echo Checking for required libraries...
%PY_CMD% -c "import PyQt6, flask, watchdog" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Dependencies already met. Launching app...
    start "" %PYW_CMD% main.py
    exit
)

:: 3. 라이브러리가 없다면 설치 시도
echo [INFO] Dependencies missing. Starting setup...

:: 가상환경이 없으면 생성
if not exist "venv" (
    echo Creating virtual environment...
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

if %ERRORLEVEL% NEQ 0 (
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
start "" %PYW_CMD% main.py
exit
