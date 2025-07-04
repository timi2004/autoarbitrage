@echo off
REM =====================================================
REM Arbitrage System Startup Script for Windows
REM =====================================================

echo.
echo ================================================
echo         ARBITRAGE SYSTEM LAUNCHER
echo ================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo    Please install Python 3.8+ and try again
    echo.
    pause
    exit /b 1
)

REM Check if we're in the right directory (look for required files)
if not exist "startup_manager.py" (
    echo ❌ startup_manager.py not found
    echo    Please run this script from the agent directory
    echo.
    pause
    exit /b 1
)

if not exist "config_manager.py" (
    echo ❌ config_manager.py not found  
    echo    Please run this script from the agent directory
    echo.
    pause
    exit /b 1
)

if not exist "mainrunner.py" (
    echo ❌ mainrunner.py not found
    echo    Please run this script from the agent directory
    echo.
    pause
    exit /b 1
)

REM Run the startup manager
echo 🚀 Starting Arbitrage System...
echo.

python startup_manager.py

REM Check the exit code
if errorlevel 1 (
    echo.
    echo ❌ Startup failed. Please check the error messages above.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ Startup completed successfully!
    echo.
)

pause