
@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Building VNA RF Analyzer EXE
echo ========================================

py -m pip install -e .
if errorlevel 1 goto error

py -m pip install pyinstaller
if errorlevel 1 goto error

py -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name VNA-RF-Analyzer ^
    --collect-all matplotlib ^
    --collect-all numpy ^
    --collect-all scipy ^
    --hidden-import tkinter ^
    --hidden-import rfanalyzer ^
    src\rfanalyzer\app.py

if errorlevel 1 goto error

echo.
echo BUILD SUCCESSFUL
echo EXE: dist\VNA-RF-Analyzer.exe
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Read the error messages above.
pause
exit /b 1
