"""
Admin Bot Training endpoints — Allow admin to proactively train the bot
with custom Q&A, conversation scripts, and bot personality settings.

These endpoints are admin-only (require Bearer token).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.core.models import Knowledge
from app.core.metrics import record_event
from app.core.settings_store import get_settings, update_settings

router = APIRouter()


# ─── Pydantic models ──────────────────────────────────────────────────────────

class TrainingQAPair(BaseModel):
    """A single question-answer pair for training the bot."""
    question_en: str = Field(..., description="Question in English")
    answer_en: str = Field(..., description="Bot response in English")
    question_ml: Optional[str] = Field("", description="Question in Malayalam (optional)")
    answer_ml: Optional[str] = Field("", description="Bot response in Malayalam (optional)")
    category: str = Field("General", description="Knowledge category")


class BulkTrainingPayload(BaseModel):
    """Submit multiple Q&A pairs at once."""
    entries: List[TrainingQAPair]


class VoiceTrainingPayload(BaseModel):
    """Payload for voice-to-train bot training."""
    audio_question_base64: str = Field(..., description="Base64-encoded audio for the question")
    audio_answer_base64: str = Field(..., description="Base64-encoded audio for the answer")
    language: str = Field("en", description="Language code: en or ml")
    category: str = Field("General", description="Knowledge category")



class TrainingResponse(BaseModel):
    """Response after adding training data."""
    status: str
    added: int
    entries: List[Dict[str, Any]]


class OutboundScriptPayload(BaseModel):
    """Configure what the bot says when placing an outbound call."""
    opening_message_en: str = Field(
        ...,
        description="English opening message for outbound calls",
        example="Hello! This is Priya from Bridgeon Skillversity. We have an exciting opportunity for you!"
    )
    opening_message_ml: Optional[str] = Field(
        "",
        description="Malayalam opening message for outbound calls"
    )
    agent_name: Optional[str] = Field(
        "Bridgeon Admissions",
        description="Name the bot introduces itself as"
    )
    purpose: Optional[str] = Field(
        "admissions",
        description="Purpose of the outbound call: admissions | follow_up | event | feedback"
    )


class BotPersonalityPayload(BaseModel):
    """Configure the bot's personality and tone."""
    bot_name: Optional[str] = Field(None, description="Bot's name (e.g. 'Priya')")
    tone: Optional[str] = Field(
        None,
        description="Communication tone: friendly | professional | formal | casual"
    )
    language_style: Optional[str] = Field(
        None,
        description="Language style: hinglish | pure_english | mixed"
    )
    custom_prompt_prefix: Optional[str] = Field(
        None,
        description="Custom instruction prefix for the bot's LLM context"
    )


class TrainingStatusResponse(BaseModel):
    total_knowledge_entries: int
    categories: Dict[str, int]
    outbound_script_configured: bool
    bot_name: str
    tone: str


# ─── Single Q&A pair ─────────────────────────────────────────────────────────

@router.post("", response_model=Dict[str, Any], summary="Add a single training Q&A pair")
async def add_training_entry(
    payload: TrainingQAPair,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    """
    Admin can add a custom Q&A pair to the knowledge base at any time.
    The bot will immediately start using this knowledge.
    No need to wait for users to ask questions first.
    """
    entry = Knowledge(
        question_en=payload.question_en,
        answer_en=payload.answer_en,
        question_ml=payload.question_ml or payload.question_en,
        answer_ml=payload.answer_ml or payload.answer_en,
        category=payload.category,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Refresh RAG vector index
    from app.core.rag import refresh_index
    refresh_index(db)

    # Audit log
    record_event("training_entry_added", "knowledge", entry.id, db)

    return {
        "status": "success",
        "message": f"Knowledge entry #{entry.id} added to bot training data.",
        "entry": {
            "id": entry.id,
            "question_en": entry.question_en,
            "answer_en": entry.answer_en,
            "category": entry.category,
            "created_at": entry.created_at.isoformat(),
        },
    }


# ─── Bulk Q&A import ──────────────────────────────────────────────────────────

@router.post("/bulk", response_model=TrainingResponse, summary="Bulk import training Q&A pairs")
async def bulk_training_import(
    payload: BulkTrainingPayload,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    """
    Import multiple Q&A pairs at once. Useful for initial bot setup or
    importing a spreadsheet of FAQ answers.
    """
    if not payload.entries:
        raise HTTPException(status_code=400, detail="No entries provided.")
    if len(payload.entries) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 entries per bulk import.")

    added = []
    for item in payload.entries:
        entry = Knowledge(
            question_en=item.question_en,
            answer_en=item.answer_en,
            question_ml=item.question_ml or item.question_en,
            answer_ml=item.answer_ml or item.answer_en,
            category=item.category,
        )
        db.add(entry)
        db.flush()
        added.append({
            "id": entry.id,
            "question_en": entry.question_en,
            "category": entry.category,
        })

    db.commit()

    # Refresh RAG index once after bulk import
    from app.core.rag import refresh_index
    refresh_index(db)

    record_event("bulk_training_import", "knowledge", len(added), db)

    return TrainingResponse(status="success", added=len(added), entries=added)


# ─── Outbound script configuration ───────────────────────────────────────────

@router.post("/outbound-script", response_model=Dict[str, Any], summary="Configure outbound call opening script")
async def set_outbound_script(
    payload: OutboundScriptPayload,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    """
    Configure what the bot says when it places an outbound call.
    This message is played immediately when the recipient picks up.
    """
    current = get_settings(db)
    updates = {
        **current,
        "outbound_opening_en": payload.opening_message_en,
        "outbound_opening_ml": payload.opening_message_ml or payload.opening_message_en,
        "outbound_agent_name": payload.agent_name or "Bridgeon Admissions",
        "outbound_purpose": payload.purpose or "admissions",
    }
    update_settings(db, updates)
    record_event("outbound_script_updated", "settings", 0, db)

    return {
        "status": "success",
        "message": "Outbound call script updated. New calls will use this opening message.",
        "opening_message_en": payload.opening_message_en,
        "agent_name": payload.agent_name,
    }


# ─── Bot personality ──────────────────────────────────────────────────────────

@router.post("/personality", response_model=Dict[str, Any], summary="Configure bot personality and tone")
async def set_bot_personality(
    payload: BotPersonalityPayload,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    """
    Customize the bot's personality: its name, tone, language style.
    Changes take effect immediately for new conversations.
    """
    current = get_settings(db)
    updates = {**current}

    if payload.bot_name:
        updates["bot_name"] = payload.bot_name
    if payload.tone:
        updates["bot_tone"] = payload.tone
    if payload.language_style:
        updates["bot_language_style"] = payload.language_style
    if payload.custom_prompt_prefix:
        updates["bot_prompt_prefix"] = payload.custom_prompt_prefix

    update_settings(db, updates)
    record_event("bot_personality_updated", "settings", 0, db)

    return {
        "status": "success",
        "message": "Bot personality updated successfully.",
        "settings": {
            "bot_name": updates.get("bot_name", "Bridgeon Assistant"),
            "tone": updates.get("bot_tone", "friendly"),
            "language_style": updates.get("bot_language_style", "pure_english"),
        },
    }


# ─── Training status ──────────────────────────────────────────────────────────

@router.get("/status", response_model=TrainingStatusResponse, summary="Get bot training status")
async def get_training_status(
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    """Overview of the bot's current training data."""
    entries = db.query(Knowledge).all()
    total = len(entries)

    categories: Dict[str, int] = {}
    for entry in entries:
        cat = entry.category or "General"
        categories[cat] = categories.get(cat, 0) + 1

    current = get_settings(db)
    outbound_configured = bool(current.get("outbound_opening_en"))

    return TrainingStatusResponse(
        total_knowledge_entries=total,
        categories=categories,
        outbound_script_configured=outbound_configured,
        bot_name=str(current.get("bot_name", "Bridgeon Assistant")),
        tone=str(current.get("bot_tone", "friendly")),
    )


@router.post("/voice", response_model=Dict[str, Any], summary="Train bot with voice input")
async def add_voice_training_entry(
    payload: VoiceTrainingPayload,
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    """
    Admin can speak a question and answer, and train the bot.
    Transcribes audio server-side (if STT provider is configured).
    If no provider configured, frontend should fallback to browser transcription.
    """
    from app.services.voice import transcribe_audio, decode_audio_base64

    # 1. Decode audio
    try:
        q_bytes = decode_audio_base64(payload.audio_question_base64)
        a_bytes = decode_audio_base64(payload.audio_answer_base64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid audio data: {exc}") from exc

    # 2. Transcribe
    try:
        transcribed_q = await transcribe_audio(q_bytes, payload.language)
        transcribed_a = await transcribe_audio(a_bytes, payload.language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc

    if not transcribed_q or not transcribed_a:
        raise HTTPException(
            status_code=503,
            detail="Server STT transcription yielded empty text. Please configure a voice provider or use browser voice training.",
        )

    # 3. Create entry
    entry = Knowledge(
        question_en=transcribed_q,
        answer_en=transcribed_a,
        question_ml=transcribed_q,
        answer_ml=transcribed_a,
        category=payload.category,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Refresh RAG vector index
    from app.core.rag import refresh_index
    refresh_index(db)

    # Audit log
    record_event("voice_training_entry_added", "knowledge", entry.id, db)

    return {
        "status": "success",
        "message": f"Voice training entry #{entry.id} added successfully.",
        "entry": {
            "id": entry.id,
            "question_en": entry.question_en,
            "answer_en": entry.answer_en,
            "category": entry.category,
            "created_at": entry.created_at.isoformat(),
        },
    }

