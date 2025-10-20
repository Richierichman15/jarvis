@echo off
REM Batch file to start the Momentum Notification Service on Windows

echo 🚀 Starting Momentum Notification Service...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if the service file exists
if not exist "momentum_notification_service.py" (
    echo ❌ momentum_notification_service.py not found
    echo Please make sure you're in the correct directory
    pause
    exit /b 1
)

REM Check environment configuration
echo 🔍 Checking environment configuration...
python start_momentum_notifications.py check
if errorlevel 1 (
    echo.
    echo ❌ Environment configuration check failed
    echo Please fix the configuration issues and try again
    pause
    exit /b 1
)

echo.
echo ✅ Environment configuration looks good
echo 🚀 Starting the service...
echo.
echo Press Ctrl+C to stop the service
echo.

REM Start the service
python start_momentum_notifications.py start

echo.
echo 👋 Service stopped
pause
