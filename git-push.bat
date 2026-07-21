@echo off
title Push Project to GitHub

echo.
echo ==========================================
echo        Pushing CrimeRakshak to GitHub
echo ==========================================
echo.

:: Initialize Git if not already done
if not exist .git (
    echo [Info] Initializing Git repository...
    git init
)

:: Set remote origin
echo [Info] Setting remote URL to https://github.com/lokojitcoder123/CrimeRakshak-NEW ...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/lokojitcoder123/CrimeRakshak-NEW

:: Add all changes to git stage
echo [Info] Staging files...
git add .

:: Commit files
echo [Info] Committing changes...
git commit -m "Initialize project and configure Clerk authentication"

:: Set branch name to main
echo [Info] Setting branch to main...
git branch -M main

:: Push to the repository
echo [Info] Pushing to GitHub (this may require you to authenticate)...
git push -u origin main --force

echo.
echo ==========================================
echo        Process Completed!
echo ==========================================
echo.
pause
