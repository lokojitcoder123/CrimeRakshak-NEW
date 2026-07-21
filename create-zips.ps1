# 100% Native Powershell Script to generate clean deployment ZIPs for Zoho Catalyst Console
$ErrorActionPreference = "Continue"

# Recursive directory copy that completely skips the excluded folder
function Copy-FilteredDir($src, $dest, $excludeName) {
    if (-not (Test-Path $dest)) { 
        New-Item -ItemType Directory -Force -Path $dest > $null 
    }
    Get-ChildItem -Path $src | ForEach-Object {
        if ($_.Name -ne $excludeName) {
            $target = Join-Path $dest $_.Name
            if ($_.PSIsContainer) {
                Copy-FilteredDir $_.FullName $target $excludeName
            } else {
                # Copy file, catching any file lock errors gracefully
                try {
                    Copy-Item $_.FullName $target -Force -ErrorAction SilentlyContinue
                } catch {}
            }
        }
    }
}

Write-Host "=== Creating clean backend.zip without venv ===" -ForegroundColor Cyan
if (Test-Path "temp_backend") { Remove-Item -Path "temp_backend" -Recurse -Force }
Copy-FilteredDir "backend" "temp_backend" "venv"

# Copy datasets/ folder into the backend zip (needed for DuckDB analytics)
Write-Host "  Copying datasets/ into backend zip..." -ForegroundColor Yellow
if (Test-Path "datasets") {
    Copy-FilteredDir "datasets" "temp_backend\datasets" ""
    Write-Host "  ✔ datasets/ included" -ForegroundColor Green
} else {
    Write-Host "  ⚠ datasets/ folder not found — analytics features may not work" -ForegroundColor Yellow
}

if (Test-Path "backend.zip") { Remove-Item -Path "backend.zip" -Force }
Compress-Archive -Path "temp_backend\*" -DestinationPath "backend.zip" -Force
Remove-Item -Path "temp_backend" -Recurse -Force
Write-Host "✔ Created backend.zip successfully!" -ForegroundColor Green

Write-Host "=== Creating clean frontend.zip without node_modules ===" -ForegroundColor Cyan
if (Test-Path "temp_frontend") { Remove-Item -Path "temp_frontend" -Recurse -Force }
Copy-FilteredDir "frontend" "temp_frontend" "node_modules"

if (Test-Path "frontend.zip") { Remove-Item -Path "frontend.zip" -Force }
Compress-Archive -Path "temp_frontend\*" -DestinationPath "frontend.zip" -Force
Remove-Item -Path "temp_frontend" -Recurse -Force
Write-Host "✔ Created frontend.zip successfully!" -ForegroundColor Green

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Done! You can now drag-and-drop backend.zip and"
Write-Host "frontend.zip into the Zoho Catalyst Console!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
