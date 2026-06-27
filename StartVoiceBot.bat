@echo off
rem ---------------------------------------------------------
rem Start VoiceBot backend (FastAPI) and frontend (Vite) and open UI
rem ---------------------------------------------------------

set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

rem ── Backend (uses venv + correct port) ───────────────────
start "Backend - FastAPI" cmd /k "cd /d %PROJECT_ROOT%\backend && .venv\Scripts\activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

rem ── Frontend (uses call to support Windows batch execution) ──
start "Frontend - Vite" cmd /k "cd /d %PROJECT_ROOT%\frontend && call npm run dev"

rem Give the servers a moment to start
ping -n 6 127.0.0.1 > nul

rem ── Open the UI in the default browser ─────────────────
start "" "http://127.0.0.1:5174/telephony"

exit
