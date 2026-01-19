@echo off
REM Advanced Web Crawler Launcher
REM This script starts the Streamlit application

echo ========================================
echo   Advanced Web Crawler ^& Backlink Analyzer
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

echo Starting application...
echo.
echo The application will open in your default browser.
echo Press Ctrl+C to stop the server.
echo.

REM Start Streamlit
streamlit run app.py

pause
