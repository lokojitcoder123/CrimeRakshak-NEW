@echo off
echo ==================================================
echo   CrimeRakshak - Build and Pack Script
echo ==================================================
echo.

echo 1. Navigating to frontend...
cd /d "%~dp0frontend"

echo 2. Building Next.js frontend...
call npm run build

echo 3. Packaging deployment zip files using python...
cd /d "%~dp0"
python zip_helper.py

echo.
echo ==================================================
echo Done! frontend.zip and backend.zip created successfully!
echo ==================================================
pause
