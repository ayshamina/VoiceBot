"""
Call log management using database (previously in-memory).
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.models import Call


def log_call(db: Session, record: Dict[str, Any]) -> Dict[str, Any]:
    """Log a call to the database."""
    call = Call(
        call_id=record.get("call_id", ""),
        caller_number=record.get("caller_number"),
        duration_seconds=record.get("duration_seconds", 0.0),
        language=record.get("language", "en"),
        outcome=record.get("outcome", "unknown"),
        call_metadata=record.get("call_metadata", {}),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call.to_dict()


def get_call(db: Session, call_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific call by ID."""
    call = db.query(Call).filter(Call.call_id == call_id).first()
    return call.to_dict() if call else None


def list_calls(db: Session, limit: Optional[int] = None) -> list[Dict[str, Any]]:
    """List all calls, optionally limited."""
    query = db.query(Call).order_by(desc(Call.timestamp))
    if limit:
        query = query.limit(limit)
    return [call.to_dict() for call in query.all()]


def get_call_count(db: Session) -> int:
    """Get total call count."""
    return db.query(Call).count()


def calls_today(db: Session) -> list[Dict[str, Any]]:
    """Get all calls from today."""
    today = datetime.now(timezone.utc).date()
    calls = db.query(Call).filter(
        Call.timestamp >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    ).all()
    return [call.to_dict() for call in calls]
