@echo off
REM Startup script for Windows

echo ========================================
echo   Agentic Honey-Pot API Server
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and configure your API keys.
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing/updating dependencies...
pip install -r requirements.txt
echo.

REM Run the server
echo Starting FastAPI server...
echo.
python main.py

pause
