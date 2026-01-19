@echo off
REM Setup script for Windows
REM Installs all required dependencies

echo ========================================
echo   Installing Dependencies
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo Installing Python packages...
pip install -r requirements.txt

echo.
echo Installing Playwright browsers (optional, for JavaScript crawling)...
echo This may take a few minutes...
playwright install chromium

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start the application, run: run.bat
echo.

pause
