@echo off
REM Discord Bot Service Starter for Windows
REM This script starts the Discord bot with automatic restart capabilities

echo Starting Discord Bot Service...
echo.
echo The bot will automatically restart if it crashes
echo Press Ctrl+C to stop the service
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if the bot file exists
if not exist "discord_jarvis_bot_full.py" (
    echo ERROR: discord_jarvis_bot_full.py not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Start the service
echo Starting bot service...
python start_discord_bot_service.py --restart-on-error --max-restarts 20

echo.
echo Bot service stopped
pause
