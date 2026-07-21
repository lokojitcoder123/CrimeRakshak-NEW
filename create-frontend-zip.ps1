# Powershell Script to generate clean frontend.zip for Zoho Catalyst Console
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Recursive copy that skips node_modules completely
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
                try {
                    Copy-Item $_.FullName $target -Force -ErrorAction SilentlyContinue
                } catch {}
            }
        }
    }
}

Write-Host "=== Packaging frontend ===" -ForegroundColor Cyan

if (Test-Path "temp_frontend") { Remove-Item -Path "temp_frontend" -Recurse -Force }
Copy-FilteredDir "frontend" "temp_frontend" "node_modules"

if (Test-Path "frontend.zip") { Remove-Item -Path "frontend.zip" -Force }
Compress-Archive -Path "temp_frontend\*" -DestinationPath "frontend.zip" -Force
Remove-Item -Path "temp_frontend" -Recurse -Force

Write-Host "Success: Created frontend.zip!" -ForegroundColor Green
