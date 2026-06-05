@echo off
title Resume Builder Pro
echo ===================================================
echo   Resume Builder Pro - PDF Generator
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
echo [SUCCESS] Resume PDF generated successfully!
echo Opening your PDF resume now...
echo.

REM Try to find and open the most recently generated PDF
for /f "delims=" %%F in ('dir /b /od *.pdf 2^>nul') do set "LATEST_PDF=%%F"
if defined LATEST_PDF (
    start "" "%LATEST_PDF%"
) else (
    echo [WARNING] No PDF file found in current directory.
)
exit
