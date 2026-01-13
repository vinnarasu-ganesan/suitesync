@echo off
pause

python app.py
REM Start the application

echo.
echo ============================================================
echo.
echo Press Ctrl+C to stop the application
echo Application will be available at: http://localhost:5000
echo.
echo Starting SuiteSync application...
echo.

)
    pause
    echo Press any key to continue anyway...
    echo Please edit .env file with your configuration.
    echo.
    copy .env.example .env
    echo Creating from .env.example...
    echo WARNING: .env file not found!
if not exist ".env" (
REM Check if .env exists

call .venv\Scripts\activate.bat
echo Activating virtual environment...
REM Activate virtual environment

)
    exit /b 1
    pause
    echo Then install requirements: pip install -r requirements.txt
    echo Please run: python -m venv .venv
    echo ERROR: Virtual environment not found!
if not exist ".venv\Scripts\activate.bat" (
REM Check if virtual environment exists

echo.
echo ============================================================
echo   SuiteSync - Test Management Application
echo ============================================================

REM SuiteSync Startup Script for Windows

