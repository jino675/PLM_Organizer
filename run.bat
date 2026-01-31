@echo off
SETLOCAL EnableDelayedExpansion

echo [PLM Organizer Launcher]
echo Checking Python installation...

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found! 
    echo Please install Python from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    pause
    exit /b
)

echo Checking Virtual Environment...
IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b
    )
    echo Virtual environment created.
)

echo Activating Virtual Environment...
call venv\Scripts\activate.bat

echo Checking/Installing Dependencies...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

echo Starting PLM Organizer...
start "" pythonw main.py
exit
