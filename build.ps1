# Build ATS resume outputs (markdown, HTML, and PDF)
# Usage: .\build.ps1

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Set-Location $Root

if (-not (Test-Path "$Root\resume.yaml")) {
    Write-Error "resume.yaml not found in $Root"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not on PATH."
}

Write-Host "Checking PyYAML..." -ForegroundColor Cyan
python -m pip install pyyaml -q

Write-Host "Building resume..." -ForegroundColor Cyan
python "$Root\build_resume.py" --pdf

if ($LASTEXITCODE -ne 0) {
    Write-Error "Resume build failed."
}

Write-Host ""
Write-Host "Publishing portfolio PDF..." -ForegroundColor Cyan
Copy-Item "$Root\resume.pdf" "$Root\Abdul-Hanan-Resume.pdf" -Force

Write-Host ""
Write-Host "Done:" -ForegroundColor Green
Write-Host "  $Root\resume.md"
Write-Host "  $Root\resume.html"
Write-Host "  $Root\resume.pdf"
Write-Host "  $Root\Abdul-Hanan-Resume.pdf"
