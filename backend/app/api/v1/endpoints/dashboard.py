"""
Dashboard endpoints for retrieving stats, logs, settings, and updating config.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


from app.core.config import settings as app_settings
from app.core.auth import issue_admin_token, require_admin
from app.core.database import get_db
from app.core.metrics import get_analytics_breakdown, get_dashboard_stats, get_recent_calls_for_dashboard
from app.core.models import Lead, KnowledgeGap
from app.core.settings_store import get_settings as get_runtime_settings
from app.core.settings_store import update_settings as update_runtime_settings
from app.core.settings_store import add_audit_log, get_audit_logs, record_knowledge_gap


router = APIRouter()


# ── Knowledge Gaps (DB-backed) ────────────────────────────────────────────────

def _get_gaps(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve all unresolved knowledge gaps from the database."""
    gaps = (
        db.query(KnowledgeGap)
        .filter(KnowledgeGap.resolved == False)  # noqa: E712
        .order_by(KnowledgeGap.frequency.desc())
        .limit(limit)
        .all()
    )
    return [g.to_dict() for g in gaps]


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    greeting_en: str = Field(..., description="Greeting message in English")
    greeting_ml: str = Field(..., description="Greeting message in Malayalam")
    voice_en: str = Field(..., description="Voice name for English TTS")
    voice_ml: str = Field(..., description="Voice name for Malayalam TTS")
    speaking_speed: str = Field(..., description="Speaking speed (slow, normal, fast)")
    escalation_number: str = Field(..., description="Escalation contact phone number")
    engine_mode: str = Field(..., description="Active engine mode (paid or open-source)")
    office_hours_enabled: bool = Field(..., description="Whether to enforce office-hours routing")
    office_hours_start: str = Field(..., description="Office hours start in HH:MM")
    office_hours_end: str = Field(..., description="Office hours end in HH:MM")
    office_timezone: str = Field(..., description="IANA timezone used for office hours")
    after_hours_message_en: str = Field(..., description="English after-hours response")
    after_hours_message_ml: str = Field(..., description="Malayalam after-hours response")
    escalation_enabled: bool = Field(..., description="Whether auto-escalation is enabled")
    auto_escalate_after_attempts: int = Field(..., ge=1, le=10, description="Unclear attempts before escalation")


class LoginRequest(BaseModel):
    username: str
    password: str


class MfaRequest(BaseModel):
    username: str
    code: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Get dashboard metrics")
async def get_stats(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    lead_count = db.query(Lead).count()
    return get_dashboard_stats(db, lead_count)


@router.get("/analytics", summary="Get analytics breakdown")
async def get_analytics(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    return get_analytics_breakdown(db)


@router.get("/recent-calls", summary="Get recent call history")
async def get_recent_calls(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    calls = get_recent_calls_for_dashboard(db, limit=10)
    if calls:
        return calls
    return [
        {
            "call_id": "—",
            "caller": "No calls yet",
            "duration": "—",
            "status": "—",
            "user_type": "—",
            "intent": "—",
            "language": "—",
            "outcome": "Simulate a call from /telephony or /bot",
            "timestamp": "",
        }
    ]


@router.get("/knowledge-gaps", summary="Get recent unanswered questions")
async def get_knowledge_gaps(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    return _get_gaps(db)


@router.delete("/knowledge-gaps/{gap_id}", summary="Resolve a knowledge gap")
async def resolve_knowledge_gap(gap_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    gap = db.query(KnowledgeGap).filter(KnowledgeGap.id == gap_id).first()
    if not gap:
        raise HTTPException(status_code=404, detail="Knowledge gap not found")
    gap.resolved = True
    db.commit()
    add_audit_log(db, f"Resolved knowledge gap: '{gap.question}'", actor="admin")
    return {"status": "success", "resolved_gap_id": gap_id}


@router.post("/login", summary="Verify admin credentials")
async def login_admin(payload: LoginRequest, db: Session = Depends(get_db)):
    if payload.username == "admin" and payload.password == "admin123":
        add_audit_log(db, f"Login attempt initiated for user: {payload.username}", actor=payload.username)
        return {"status": "mfa_required", "message": "Verification code sent to registered device"}

    add_audit_log(db, f"Failed login attempt for user: {payload.username}", actor="System")
    raise HTTPException(status_code=401, detail="Invalid username or password")


@router.post("/mfa", summary="Verify MFA code")
async def verify_mfa(payload: MfaRequest, db: Session = Depends(get_db)):
    if payload.code == "123456":
        token = issue_admin_token(payload.username)
        add_audit_log(db, "MFA verification successful. Admin session started.", actor=payload.username)
        return {"status": "success", "token": token}

    add_audit_log(db, f"MFA verification failed for user: {payload.username}", actor="System")
    raise HTTPException(status_code=400, detail="Invalid verification code")


@router.get("/audit-logs", summary="Get admin audit trail")
async def retrieve_audit_logs(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    logs = get_audit_logs(db)
    # Normalize field names for frontend compatibility
    normalized = []
    for log in logs:
        normalized.append({
            "id": log.get("id"),
            "timestamp": log.get("timestamp"),
            "action": log.get("action"),
            "actor": log.get("actor", "system"),
            "target": log.get("target"),
            "details": log.get("details"),
        })
    return normalized


@router.get("/settings", summary="Get current configurations")
async def get_settings(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    return get_runtime_settings(db)


@router.put("/settings", summary="Update bot configurations")
async def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    settings = update_runtime_settings(db, payload.model_dump())
    add_audit_log(db, "Updated Call Configuration settings", actor="admin")
    return {
        "status": "success",
        "message": "Configurations updated successfully",
        "settings": settings,
    }


@router.get("/integrations", summary="Get multi-channel integrations status")
async def get_integrations_status(_: str = Depends(require_admin)):
    """
    Checks backend environment variables and returns which integrations
    are configured (Twilio, Exotel, SMTP, WhatsApp).
    """
    return [
        {
            "icon": "💬",
            "name": "WhatsApp Business",
            "status": "Active" if app_settings.twilio_configured and app_settings.TWILIO_WHATSAPP_NUMBER else "Not configured",
            "ok": bool(app_settings.twilio_configured and app_settings.TWILIO_WHATSAPP_NUMBER),
            "desc": "Send rich messages, PDFs, brochures",
        },
        {
            "icon": "📱",
            "name": "SMS (Twilio/Exotel)",
            "status": "Active" if app_settings.twilio_configured or app_settings.exotel_configured else "Not configured",
            "ok": bool(app_settings.twilio_configured or app_settings.exotel_configured),
            "desc": "Post-call confirmations, reminders",
        },
        {
            "icon": "📧",
            "name": "Email (SMTP)",
            "status": "Active" if app_settings.smtp_configured else "Not configured",
            "ok": bool(app_settings.smtp_configured),
            "desc": "Lead alerts, daily reports, weekly metrics",
        },
        {
            "icon": "📞",
            "name": "Voice (Twilio/Exotel)",
            "status": "Active" if app_settings.exotel_configured or app_settings.twilio_configured else "Not configured",
            "ok": bool(app_settings.exotel_configured or app_settings.twilio_configured),
            "desc": "Inbound & outbound voice calls",
        },
    ]

