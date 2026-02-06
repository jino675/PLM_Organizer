@echo off
setlocal

:: Check for Admin rights (Auto-Elevation)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Ensure we are in the script directory
cd /d "%~dp0"

echo [PLM Organizer Builder]

:: 0. Kill running instances
echo [*] Checking for running instances...
taskkill /F /IM PLM_Organizer.exe /T
timeout /t 3 /nobreak >nul

:: 1. Check for PyInstaller
if not exist "venv\Scripts\pyinstaller.exe" (
    echo [!] PyInstaller not found. Installing...
    venv\Scripts\pip install pyinstaller
)

:: 2. Clean previous builds / Verify Lock
echo [*] Cleaning old build files...
if exist dist\PLM_Organizer.exe (
    del dist\PLM_Organizer.exe >nul 2>&1
    if exist dist\PLM_Organizer.exe (
        echo.
        echo [!] FATAL ERROR: Cannot delete 'dist\PLM_Organizer.exe'.
        echo [!] The file is locked or running by another user/process.
        echo [!] Please close it manually and run build.bat again.
        echo.
        pause
        exit /b 1
    )
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 3. Run Build (Using Spec File to include VERSION)
echo [*] Building EXE...
venv\Scripts\pyinstaller --clean PLM_Organizer.spec

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build Failed!
    pause
    exit /b
)

echo =======================
echo [SUCCESS] Build Complete!
echo EXE Location: dist\PLM_Organizer.exe
echo =======================
pause
