"""
Database models for all entities: Knowledge, Leads, Calls, Audit Logs, Settings.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON
from app.core.database import Base


class Knowledge(Base):
    """FAQ knowledge base entries."""
    __tablename__ = "knowledge"

    id = Column(Integer, primary_key=True, index=True)
    question_en = Column(String(500), nullable=False)
    answer_en = Column(Text, nullable=False)
    question_ml = Column(String(500), nullable=True)
    answer_ml = Column(Text, nullable=True)
    category = Column(String(100), default="General", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "question_en": self.question_en,
            "answer_en": self.answer_en,
            "question_ml": self.question_ml,
            "answer_ml": self.answer_ml,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Lead(Base):
    """Lead capture records with consent and language preferences."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    course = Column(String(255), nullable=False)
    consent_whatsapp = Column(Boolean, nullable=True)
    language = Column(String(10), default="en", nullable=False)
    source = Column(String(50), default="bot", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "course": self.course,
            "consent_whatsapp": self.consent_whatsapp,
            "language": self.language,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
        }


class Call(Base):
    """Call log entries for metrics and auditing."""
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(50), unique=True, nullable=False, index=True)
    caller_number = Column(String(20), nullable=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    outcome = Column(String(50), default="unknown", nullable=False)  # e.g., "lead_captured", "escalated", "completed"
    call_metadata = Column(JSON, default=dict, nullable=False)  # Additional call data
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "call_id": self.call_id,
            "caller_number": self.caller_number,
            "duration_seconds": self.duration_seconds,
            "language": self.language,
            "outcome": self.outcome,
            "metadata": self.call_metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class AuditLog(Base):
    """Audit logs for all admin actions and key operations."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(100), default="system", nullable=False)
    target = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "actor": self.actor,
            "target": self.target,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class Setting(Base):
    """Admin configuration settings."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat(),
        }


class Event(Base):
    """Event tracking for analytics and monitoring."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    data = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class KnowledgeGap(Base):
    """Questions asked by callers that the bot could not answer from the knowledge base."""
    __tablename__ = "knowledge_gaps"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(1000), nullable=False)
    frequency = Column(Integer, default=1, nullable=False)
    category = Column(String(100), default="General", nullable=False)
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "frequency": self.frequency,
            "category": self.category,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "resolved": self.resolved,
        }


class BotSession(Base):
    """Session state for the bot conversational pipeline."""
    __tablename__ = "bot_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    session_data = Column(JSON, default=dict, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "session_data": self.session_data,
            "updated_at": self.updated_at.isoformat(),
        }


class Campaign(Base):
    """Outbound Call/WhatsApp/SMS/Email campaigns."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), default="voice", nullable=False)  # "voice", "whatsapp", "sms", "email"
    script = Column(Text, nullable=True)
    schedule_time = Column(String(100), nullable=True)
    status = Column(String(50), default="Draft", nullable=False)  # "Draft", "Scheduled", "Running", "Paused", "Completed"
    retry_attempts = Column(Integer, default=3, nullable=False)
    consent_required = Column(Boolean, default=True, nullable=False)
    dnd_compliance = Column(Boolean, default=True, nullable=False)
    contacted = Column(Integer, default=0, nullable=False)
    answered = Column(Integer, default=0, nullable=False)
    converted = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "channel": self.channel,
            "script": self.script,
            "schedule_time": self.schedule_time,
            "status": self.status,
            "retry_attempts": self.retry_attempts,
            "consent_required": self.consent_required,
            "dnd_compliance": self.dnd_compliance,
            "contacted": self.contacted,
            "answered": self.answered,
            "converted": self.converted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


