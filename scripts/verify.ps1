# Bridgeon VoiceBot — local verification script (Phase 12)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Verifying backend dependencies and tests"
Push-Location (Join-Path $root "backend")
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . .venv\Scripts\Activate.ps1
}
python -m pytest tests -q
Pop-Location

Write-Host "==> Verification complete"
