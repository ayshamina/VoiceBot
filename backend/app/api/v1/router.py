"""
API v1 — Main Router
Aggregates all endpoint routers for version 1 of the API.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import dashboard, bot, health, knowledge, leads, telephony, voice, training, campaigns

api_router = APIRouter()

# ── Health ────────────────────────────────────────────────────────────────────
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# ── Dashboard ─────────────────────────────────────────────────────────────────
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# ── Bot Simulation ─────────────────────────────────────────────────────────────
api_router.include_router(bot.router, prefix="/bot", tags=["Bot"])

# ── Telephony (Inbound + Outbound — Exotel + Sarvam AI) ───────────────────────
api_router.include_router(telephony.router, prefix="/telephony", tags=["Telephony"])

# ── Knowledge Base ─────────────────────────────────────────────────────────────
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])

# ── Leads ───────────────────────────────────────────────────────────────────────
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])

# ── Voice (STT / TTS — Sarvam AI + OpenAI fallback) ───────────────────────────
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])

# ── Admin Bot Training ─────────────────────────────────────────────────────────
api_router.include_router(training.router, prefix="/training", tags=["Training"])

# ── Outbound Campaigns ────────────────────────────────────────────────────────
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])

