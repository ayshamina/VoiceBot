"""
Runtime settings store for admin-controlled bot configuration (Database-backed).
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.models import Setting, AuditLog, KnowledgeGap


DEFAULT_SETTINGS: Dict[str, Any] = {
    "greeting_en": "Hello, thank you for calling Bridgeon. How may I assist you today?",
    "greeting_ml": "ഹലോ, ബ്രിഡ്ജിയോണിലേക്ക് വിളിച്ചതിന് നന്ദി. ഞാൻ ഇന്ന് നിങ്ങളെ എങ്ങനെയാണ് സഹായിക്കേണ്ടത്?",
    "voice_en": "en-IN-Wavenet-A (Female)",
    "voice_ml": "ml-IN-Standard-A (Female)",
    "speaking_speed": "normal",
    "escalation_number": "+919876543210",
    "engine_mode": "paid",
    "office_hours_enabled": False,
    "office_hours_start": "09:00",
    "office_hours_end": "18:00",
    "office_timezone": "Asia/Kolkata",
    "after_hours_message_en": (
        "Our admissions team is currently outside office hours. "
        "Please leave your name and phone number, and we will call you back during working hours."
    ),
    "after_hours_message_ml": (
        "Admissions team ippol office hours-il alla. "
        "Dayavayi ningalude peru, phone number parayuka; working hours-il njangal thirichu vilikkum."
    ),
    "escalation_enabled": True,
    "auto_escalate_after_attempts": 3,
}


def _ensure_defaults(db: Session):
    """Ensure all default settings exist in database."""
    for key, value in DEFAULT_SETTINGS.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            setting = Setting(key=key, value=str(value))
            db.add(setting)
    db.commit()


def get_settings(db: Session) -> Dict[str, Any]:
    """Get all settings from database."""
    _ensure_defaults(db)
    settings = {}
    rows = db.query(Setting).all()
    for row in rows:
        # Try to parse value back to original type
        value = row.value
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        settings[row.key] = value
    return settings


def update_settings(db: Session, updated: Dict[str, Any]) -> Dict[str, Any]:
    """Update settings in database."""
    for key, value in updated.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if existing:
            existing.value = str(value)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            new_setting = Setting(key=key, value=str(value))
            db.add(new_setting)
    db.commit()
    return get_settings(db)


def _parse_minutes(value: str) -> int:
    """Parse time string (HH:MM) to minutes."""
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def is_inside_office_hours(db: Session, now: Optional[datetime] = None) -> bool:
    """Check if current time is within office hours."""
    settings = get_settings(db)
    if not settings.get("office_hours_enabled"):
        return True

    try:
        tz = ZoneInfo(str(settings.get("office_timezone") or "Asia/Kolkata"))
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("Asia/Kolkata")

    local_now = now.astimezone(tz) if now else datetime.now(tz)
    current_minutes = local_now.hour * 60 + local_now.minute
    start_minutes = _parse_minutes(str(settings.get("office_hours_start") or "09:00"))
    end_minutes = _parse_minutes(str(settings.get("office_hours_end") or "18:00"))

    if start_minutes <= end_minutes:
        return start_minutes <= current_minutes < end_minutes
    return current_minutes >= start_minutes or current_minutes < end_minutes


def get_audit_logs(db: Session, limit: int = 50) -> list[Dict[str, Any]]:
    """Get audit logs from database."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]


def add_audit_log(db: Session, action: str, actor: str = "Admin", target: Optional[str] = None, details: Optional[str] = None):
    """Add an audit log entry."""
    log = AuditLog(
        action=action,
        actor=actor,
        target=target,
        details=details,
    )
    db.add(log)
    db.commit()


def record_knowledge_gap(db: Session, question: str, category: str = "General") -> None:
    """Record or increment a knowledge gap when the bot cannot answer a question."""
    if not question or len(question.strip()) < 5:
        return
    question = question.strip()
    existing = db.query(KnowledgeGap).filter(KnowledgeGap.question == question).first()
    if existing:
        existing.frequency += 1
        existing.last_seen = datetime.now(timezone.utc)
    else:
        gap = KnowledgeGap(question=question, category=category)
        db.add(gap)
    db.commit()
