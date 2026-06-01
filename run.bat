@echo off
title Resume Generator
echo ===================================================
echo   Generating Sejal Bhagat's Resume PDF...
echo ===================================================
echo.

python generate_resume.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to compile resume!
    echo Please ensure Python and the 'reportlab' library are installed.
    echo You can install dependencies using: pip install -r requirements.txt
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Sejal_Bhagat_Resume.pdf generated successfully!
echo Opening your PDF resume now...
echo.

start "" "Sejal_Bhagat_Resume.pdf"
exit
