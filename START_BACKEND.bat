@echo off
echo ========================================
echo   Cardiac AI Backend Server Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version

echo.
echo [2/4] Checking if virtual environment exists...
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    echo Virtual environment created successfully!
)

echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/4] Installing/Updating dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo ========================================
echo   Starting Backend Server...
echo ========================================
echo.
echo Server will be available at:
echo   http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py

pause
