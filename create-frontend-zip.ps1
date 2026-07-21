# Powershell Script to generate clean frontend.zip using zip_helper.py
$ErrorActionPreference = "Continue"

Write-Host "=== Creating clean frontend.zip ===" -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
python zip_helper.py

Write-Host "✔ Done!" -ForegroundColor Green
