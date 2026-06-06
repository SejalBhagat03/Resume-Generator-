@echo off
title Resume Builder Pro
setlocal enabledelayedexpansion

echo ===================================================
echo        📄 RESUME BUILDER PRO - LAUNCHER 🚀
echo ===================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system!
    echo Please download and install Python 3.10+ from: https://www.python.org/
    echo Make sure to check the option "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check virtual environment
if not exist ".venv" (
    echo [SETUP] Setting up a virtual environment (.venv)...
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SETUP] Virtual environment created successfully.
)

:: 3. Activate Virtual Environment
echo [LAUNCH] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

:: 4. Install/Update requirements
echo [SETUP] Checking & updating dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

:: 5. Launch the Streamlit App
echo.
echo ===================================================
echo   [SUCCESS] App is ready! Starting Streamlit...
echo   If the browser doesn't open automatically, go to:
echo   http://localhost:8501
echo ===================================================
echo.

python -m streamlit run app.py

pause
