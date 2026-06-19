"""
Health check endpoints.

GET /api/v1/health        — lightweight liveness probe
GET /api/v1/health/ready  — readiness probe (checks subsystem availability)
"""
import platform
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.voice import get_voice_status

router = APIRouter()

# Track server start time for uptime calculation
_START_TIME: float = time.monotonic()


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    uptime_seconds: float
    timestamp: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict


@router.get("", response_model=HealthResponse, summary="Liveness probe")
async def health_check():
    """
    Returns 200 OK as long as the server process is running.
    Use this as a liveness probe in Docker / Kubernetes.
    """
    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        uptime_seconds=round(time.monotonic() - _START_TIME, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment="development" if settings.DEBUG else "production",
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Checks that all downstream services are reachable.
    """
    voice = get_voice_status()
    checks: dict = {
        "api": "ok",
        "database": "ok",
        "llm": voice["llm"],
        "stt": voice["stt"],
        "tts": voice["tts"],
        "telephony": voice["telephony"],
        "openai": "configured" if voice["openai_configured"] else "not_configured",
        "twilio": "configured" if voice["twilio_configured"] else "not_configured",
    }
    
    # Test database connection
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    all_critical_ok = checks["api"] == "ok" and checks["database"] == "ok"
    return ReadinessResponse(
        status="ready" if all_critical_ok else "degraded",
        checks=checks,
    )
