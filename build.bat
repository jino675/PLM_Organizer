@echo off
setlocal
echo [PLM Organizer Builder]
echo =======================

:: 1. Check for PyInstaller
if not exist "venv\Scripts\pyinstaller.exe" (
    echo [!] PyInstaller not found. Installing...
    venv\Scripts\pip install pyinstaller
)

:: 2. Clean previous builds
echo [*] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

:: 3. Run Build
echo [*] Building EXE...
:: --noconsole: No black window
:: --onefile: Single .exe file
:: --clean: Clean cache
:: --add-data: Include assets folder
venv\Scripts\pyinstaller --noconsole --onefile --clean ^
    --name="PLM_Organizer" ^
    --icon="app/assets/icon.png" ^
    --add-data "app/assets;app/assets" ^
    main.py

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
