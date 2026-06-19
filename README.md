# Bridgeon Voice Call Assistant

> AI-powered, telephony-integrated voice bot for Bridgeon Skillversity — v4.0

---

## Project Structure

```
VoiceBot/
├── backend/                  # FastAPI Python backend
│   ├── main.py               # App entry point
│   ├── requirements.txt      # Python dependencies
│   ├── tests/                # Pytest API tests
│   ├── .env.example          # Environment variable template
│   └── app/
│       ├── core/
│       │   ├── config.py     # Settings loaded from .env
│       │   ├── auth.py       # Admin token auth
│       │   ├── metrics.py    # Live event tracking
│       │   ├── call_store.py # Shared telephony call log
│       │   ├── rag.py        # RAG prototype
│       │   ├── settings_store.py
│       │   └── telephony.py  # STT/TTS stubs
│       └── api/v1/endpoints/
│           ├── health.py
│           ├── dashboard.py
│           ├── bot.py
│           ├── telephony.py
│           ├── knowledge.py
│           └── leads.py
│
├── frontend/                 # Vite + React frontend
│   └── src/
│       ├── pages/
│       │   ├── LandingPage.jsx
│       │   ├── Dashboard.jsx
│       │   ├── BotSimulator.jsx
│       │   └── TelephonySimulator.jsx
│       ├── services/api.js
│       └── hooks/useHealth.js
│
├── scripts/
│   └── verify.ps1            # Run backend tests
├── bridgeon_voicebot_prd.md
├── task.md
└── README.md
```

---

## Quick Start

### Prerequisites

| Tool    | Minimum Version |
|---------|-----------------|
| Python  | 3.11+           |
| Node.js | 20+             |
| npm     | 10+             |

---

### Start both servers (recommended)

```powershell
.\scripts\start-dev.ps1
```

This opens two terminals: backend on **:8000** and frontend on **:5173**.

### 1. Backend — FastAPI (manual)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **API root:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **Health:** http://localhost:8000/api/v1/health

---

### 2. Frontend — Vite + React

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

- **App:** http://localhost:5173
- **Admin:** http://localhost:5173/admin (`admin` / `admin123`, MFA `123456`)
- **Bot simulator:** http://localhost:5173/bot
- **Telephony simulator:** http://localhost:5173/telephony

All `/api/*` requests proxy to `http://localhost:8000`.

---

### 3. Run tests

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest tests -v
```

Or from the project root:

```powershell
.\scripts\verify.ps1
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | No | Liveness probe |
| GET | `/api/v1/health/ready` | No | Readiness probe |
| POST | `/api/v1/bot/chat` | No | Bot conversation |
| POST | `/api/v1/telephony/inbound` | No | Simulate inbound call |
| GET | `/api/v1/knowledge` | No | List/search FAQs |
| POST | `/api/v1/dashboard/login` | No | Admin login |
| POST | `/api/v1/dashboard/mfa` | No | Admin MFA |
| GET | `/api/v1/dashboard/stats` | Yes | Live metrics |
| GET | `/api/v1/dashboard/analytics` | Yes | Analytics breakdown |
| PUT | `/api/v1/dashboard/settings` | Yes | Update bot config |
| POST | `/api/v1/knowledge` | Yes | Create FAQ |
| GET | `/api/v1/leads` | Yes | List leads |

Protected routes require `Authorization: Bearer <token>` from MFA login.

---

## Development Phases

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | Scaffold — backend + frontend running | ✅ Complete |
| 2 | Admin dashboard shell with live data | ✅ Complete |
| 3 | Voice flow simulation & basic bot pipeline | ✅ Complete |
| 4 | Knowledge base CRUD & FAQ response | ✅ Complete |
| 5 | Lead capture & consent flow | ✅ Complete |
| 6 | Bilingual support (English + Malayalam) | ✅ Complete |
| 7 | Telephony integration stub | ✅ Complete |
| 8 | RAG retrieval prototype | ✅ Complete |
| 9 | Engine/settings toggles & admin config | ✅ Complete |
| 10 | Metrics dashboard & monitoring | ✅ Complete |
| 11 | Security & audit basics | ✅ Complete |
| 12 | Production readiness & test harness | ✅ Complete |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python · FastAPI · Uvicorn · Pydantic |
| Frontend | React 18 · Vite 5 · React Router |
| Storage | In-memory (prototype) |
| AI | Local RAG + keyword FAQ matching |
| Telephony | Stub adapter (Twilio-ready interface) |

---

## Environment Variables

See [`backend/.env.example`](./backend/.env.example). Copy to `.env` before running the backend.
