# Powershell Script to generate clean deployment ZIPs using Robocopy
$ErrorActionPreference = "Continue"

Write-Host "=== Creating clean backend.zip ===" -ForegroundColor Cyan
if (Test-Path "temp_backend") { Remove-Item -Path "temp_backend" -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path "temp_backend" -Force > $null
robocopy backend temp_backend /E /XD venv .venv __pycache__ logs /NJH /NJS /NDL /NC /NS > $null

if (Test-Path "datasets") {
    Write-Host "  Copying datasets/ into backend zip..." -ForegroundColor Yellow
    robocopy datasets temp_backend\datasets /E /NJH /NJS /NDL /NC /NS > $null
}

if (Test-Path "backend.zip") { Remove-Item -Path "backend.zip" -Force }
Compress-Archive -Path "temp_backend\*" -DestinationPath "backend.zip" -Force
Remove-Item -Path "temp_backend" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✔ Created backend.zip successfully!" -ForegroundColor Green

Write-Host "=== Creating clean frontend.zip ===" -ForegroundColor Cyan
if (Test-Path "temp_frontend") { Remove-Item -Path "temp_frontend" -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path "temp_frontend" -Force > $null
robocopy frontend temp_frontend /E /XD node_modules /NJH /NJS /NDL /NC /NS > $null

if (Test-Path "frontend.zip") { Remove-Item -Path "frontend.zip" -Force }
Compress-Archive -Path "temp_frontend\*" -DestinationPath "frontend.zip" -Force
Remove-Item -Path "temp_frontend" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✔ Created frontend.zip successfully!" -ForegroundColor Green

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Done! frontend.zip and backend.zip are ready!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
