# Start backend + frontend for local development
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "Starting Bridgeon VoiceBot (backend :8000 + frontend :5173)..."

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backend'; if (Test-Path '.venv\Scripts\Activate.ps1') { . .venv\Scripts\Activate.ps1 }; uvicorn main:app --reload --host 127.0.0.1 --port 8000"
) -WindowStyle Normal

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontend'; npm run dev"
) -WindowStyle Normal

Write-Host "Done. Open http://127.0.0.1:5173/ when both terminals show ready."
