@echo off
echo ==================================================
echo   CrimeRakshak - Build and Pack Script
echo ==================================================
echo.

echo 1. Navigating to frontend...
cd /d "%~dp0frontend"

echo 2. Installing frontend dependencies...
call npm install --no-audit --no-fund

echo 3. Building Next.js frontend with new API URL...
call npm run build

echo 4. Packaging deployment zip files...
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File create-zips.ps1

echo.
echo ==================================================
echo Done! Now upload the backend.zip and frontend.zip
echo files directly into your Zoho Catalyst Console.
echo ==================================================
pause
