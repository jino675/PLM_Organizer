@echo off
setlocal
echo [PLM Organizer Builder]
echo =======================

:: 0. Kill running instances
echo [*] Stopping running instances...
taskkill /F /IM PLM_Organizer.exe /T 2>nul
timeout /t 1 /nobreak >nul

:: 1. Check for PyInstaller
if not exist "venv\Scripts\pyinstaller.exe" (
    echo [!] PyInstaller not found. Installing...
    venv\Scripts\pip install pyinstaller
)

:: 2. Clean previous builds
echo [*] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 3. Run Build (Using Spec File to include VERSION)
echo [*] Building EXE...
venv\Scripts\pyinstaller --clean --noconsole PLM_Organizer.spec

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
