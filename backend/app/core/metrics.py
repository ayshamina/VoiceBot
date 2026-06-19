"""
Runtime metrics and event tracking for dashboard analytics (Phase 10 - Database-backed).
"""
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.models import Event, Call
from app.core.call_store import calls_today, get_call_count, list_calls


_INTENT_LABELS = {
    "greeting": "General Greeting Only",
    "explore_courses": "Course Info & Duration",
    "faq_response": "Course Info & Duration",
    "rag_response": "Course Info & Duration",
    "ask_fee_callback": "Fee Structure",
    "placement_queries": "Placement & Salary Queries",
    "course_info": "Course Info & Duration",
    "check_schedule": "Batch Schedule & Timings",
    "check_deadline": "Batch Schedule & Timings",
    "student_check_in": "Batch Schedule & Timings",
    "consent_granted": "Lead Captured + Consent",
    "consent_denied": "Lead Captured + Consent",
    "escalated": "Escalated to Human",
    "after_hours": "After-Hours Callback",
    "unclear_user_type": "General Greeting Only",
}


def record_event(
    event_type: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    db: Optional[Session] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Record an event in the database."""
    if not db:
        return {}
    
    event = Event(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        data=data or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event.to_dict()


def record_bot_turn(
    db: Session,
    session_id: str,
    intent: str,
    user_type: str,
    language: str,
    outcome: str,
    escalated: bool = False,
) -> None:
    """Record a bot turn event."""
    if escalated:
        outcome = "escalated"
    
    record_event(
        event_type="bot_turn",
        entity_type="session",
        data={
            "session_id": session_id,
            "intent": intent,
            "user_type": user_type,
            "language": language,
            "outcome": outcome,
        },
        db=db,
    )


def record_telephony_call(db: Session, call_record: Dict[str, Any], bot_meta: Optional[Dict[str, Any]] = None) -> None:
    """Record a telephony call event."""
    meta = bot_meta or {}
    record_event(
        event_type="telephony_call",
        entity_type="call",
        data={
            "call_id": call_record.get("call_id"),
            "session_id": call_record.get("session_id"),
            "intent": meta.get("intent", "greeting"),
            "user_type": meta.get("user_type", "unknown"),
            "language": call_record.get("language", "en"),
            "outcome": meta.get("outcome", "completed"),
        },
        db=db,
    )


def _resolution_stats(db: Session) -> Dict[str, float]:
    """Calculate resolution and escalation rates."""
    relevant = db.query(Event).filter(Event.event_type.in_(["bot_turn", "telephony_call"])).all()
    if not relevant:
        return {"resolution_rate": 0.0, "escalation_rate": 0.0}

    escalated = sum(1 for event in relevant if event.data.get("outcome") == "escalated")
    resolved = sum(
        1
        for event in relevant
        if event.data.get("outcome") in ("resolved", "completed", "lead_captured")
    )
    total = len(relevant)
    return {
        "resolution_rate": round((resolved / total) * 100, 1),
        "escalation_rate": round((escalated / total) * 100, 1),
    }


def get_dashboard_stats(db: Session, lead_count: int) -> Dict[str, Any]:
    """Get dashboard statistics."""
    rates = _resolution_stats(db)
    today_calls = calls_today(db)
    all_calls = list_calls(db)
    
    return {
        "stats": {
            "total_calls": len(today_calls) if today_calls else get_call_count(db),
            "total_calls_all_time": get_call_count(db),
            "leads_captured": lead_count,
            "resolution_rate": rates["resolution_rate"],
            "escalation_rate": rates["escalation_rate"],
            "bot_interactions": db.query(Event).filter(Event.event_type == "bot_turn").count(),
        },
        "active_calls": _active_calls(db),
    }


def _active_calls(db: Session) -> List[Dict[str, Any]]:
    """Get active calls."""
    recent = list_calls(db, limit=1)
    if not recent:
        return []
    latest = recent[0]
    if latest.get("outcome") not in ("in-progress", "in_progress"):
        return []

    raw_secs = latest.get("duration_seconds", 0) or 0
    mins, secs = divmod(int(raw_secs), 60)
    duration_str = f"{mins}m {secs}s" if mins else f"{secs}s"

    meta = latest.get("metadata") or {}
    return [
        {
            "call_id": latest["call_id"],
            "caller": latest.get("caller_number", "Unknown"),
            "duration": duration_str,
            "status": latest.get("outcome", "in-progress"),
            "user_type": meta.get("user_type", "unknown"),
            "intent": meta.get("intent", "greeting"),
            "language": "Malayalam" if latest.get("language") == "ml" else "English",
        }
    ]



def get_analytics_breakdown(db: Session) -> Dict[str, Any]:
    """Get analytics breakdown by outcome, language, and intent."""
    relevant = db.query(Event).filter(Event.event_type.in_(["bot_turn", "telephony_call"])).all()
    total = len(relevant) or 1

    outcome_counter = Counter(event.data.get("outcome", "unknown") for event in relevant)
    language_counter = Counter(event.data.get("language", "en") for event in relevant)
    intent_counter = Counter(event.data.get("intent", "unknown") for event in relevant)

    outcomes = [
        {
            "label": "Resolved by Bot",
            "count": outcome_counter.get("resolved", 0) + outcome_counter.get("completed", 0),
            "pct": round(
                ((outcome_counter.get("resolved", 0) + outcome_counter.get("completed", 0)) / total) * 100
            ),
        },
        {
            "label": "Lead Captured + Consent",
            "count": outcome_counter.get("lead_captured", 0),
            "pct": round((outcome_counter.get("lead_captured", 0) / total) * 100),
        },
        {
            "label": "Escalated to Human",
            "count": outcome_counter.get("escalated", 0),
            "pct": round((outcome_counter.get("escalated", 0) / total) * 100),
        },
        {
            "label": "Call Abandoned",
            "count": outcome_counter.get("abandoned", 0),
            "pct": round((outcome_counter.get("abandoned", 0) / total) * 100),
        },
    ]

    en_count = language_counter.get("en", 0)
    ml_count = language_counter.get("ml", 0)
    lang_total = en_count + ml_count or 1

    top_intents = []
    for intent, count in intent_counter.most_common(5):
        top_intents.append(
            {
                "label": _INTENT_LABELS.get(intent, str(intent).replace("_", " ").title()),
                "intent": intent,
                "count": count,
                "pct": round((count / total) * 100),
            }
        )

    return {
        "outcomes": outcomes,
        "languages": {
            "en": {"count": en_count, "pct": round((en_count / lang_total) * 100)},
            "ml": {"count": ml_count, "pct": round((ml_count / lang_total) * 100)},
        },
        "top_intents": top_intents,
        "total_events": len(relevant),
    }


def get_recent_calls_for_dashboard(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent calls for dashboard display."""
    rows: List[Dict[str, Any]] = []
    for call in list_calls(db, limit=limit):
        rows.append(
            {
                "call_id": call["call_id"],
                "caller": call.get("caller_number", "Unknown"),
                "duration": f"{call.get('duration_seconds', 0):.0f}s",
                "status": call.get("outcome", "completed"),
                "user_type": call.get("metadata", {}).get("user_type", "unknown"),
                "intent": call.get("metadata", {}).get("intent", "greeting"),
                "language": "Malayalam" if call.get("language") == "ml" else "English",
                "outcome": call.get("outcome", "Completed"),
                "timestamp": call["timestamp"],
            }
        )
    return rows
