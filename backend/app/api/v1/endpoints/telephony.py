"""
Telephony endpoints — Real inbound + outbound calls via Exotel,
with Sarvam AI for STT/TTS and the bot conversational pipeline.

Inbound call flow (Exotel webhook → /telephony/inbound/webhook):
  1. Exotel dials your virtual number → hits /telephony/inbound/webhook
  2. Backend responds with ExoML (XML) to play TTS greeting
  3. Caller speaks → Exotel records → hits /telephony/inbound/recording
  4. Backend sends audio to Sarvam AI STT → gets transcript
  5. Bot pipeline processes transcript → generates response text
  6. Backend calls Sarvam AI TTS → creates audio URL or plays it

Outbound call flow (admin triggers → /telephony/outbound):
  1. Admin sends POST /telephony/outbound with phone number
  2. Backend calls Exotel REST API to dial the number
  3. Exotel connects the call and hits /telephony/outbound/webhook
  4. Bot plays the outbound campaign message via TTS
"""
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import Response, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.endpoints.bot import ChatPayload, chat
from app.core.config import settings
from app.core.database import get_db
from app.core.call_store import get_call, list_calls, log_call
from app.core.metrics import record_telephony_call
from app.core.telephony import StubTelephonyAdapter
from app.services.voice import get_voice_status, synthesize_speech, transcribe_audio
from app.core.audio_cache import store_audio, get_audio
from app.core import telephony_debug as tlog

import httpx
import os
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter()
_STUB = StubTelephonyAdapter()


# ─── Helper: ExoML response for Exotel ───────────────────────────────────────

def _exoml_play_audio(audio_url: str, record_url: Optional[str] = None) -> str:
    """
    Generate ExoML XML for Exotel to PLAY a pre-generated TTS audio URL
    and optionally record the caller's response.
    This gives much better voice quality than Exotel's built-in <Say>.
    """
    record_section = ""
    if record_url:
        record_section = f"""
    <Record action="{record_url}" maxLength="120" timeout="3" finishOnKey="#" playBeep="true"/>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>{record_section}
</Response>"""


def _exoml_say(message: str, record_url: Optional[str] = None) -> str:
    """
    Fallback: Generate ExoML XML using Exotel's built-in <Say> TTS.
    Used when Sarvam TTS is unavailable.
    """
    record_section = ""
    if record_url:
        record_section = f"""
    <Record action="{record_url}" maxLength="120" timeout="3" finishOnKey="#" playBeep="true"/>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>{message}</Say>{record_section}
</Response>"""


def _exoml_hangup(message: str = "", audio_url: Optional[str] = None) -> str:
    """Generate ExoML to play/say a message and hang up."""
    if audio_url:
        play_part = f"<Play>{audio_url}</Play>"
    elif message:
        play_part = f"<Say>{message}</Say>"
    else:
        play_part = ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {play_part}
    <Hangup/>
</Response>"""


async def _generate_play_url(text: str, language: str = "en") -> Optional[str]:
    """
    Generate TTS audio via Sarvam AI, store it in the audio cache,
    and return a public URL that Exotel can fetch with <Play>.
    Returns None if TTS generation fails.
    """
    try:
        audio_bytes = await synthesize_speech(text, language)
        if audio_bytes:
            audio_id = store_audio(audio_bytes, "audio/wav")
            play_url = f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/audio/{audio_id}"
            tlog.debug(f"TTS audio cached", audio_id=audio_id, text_preview=text[:60])
            return play_url
    except Exception as e:
        tlog.error(f"TTS generation failed: {e}")
    return None


def _build_exoml_response(text: str, audio_url: Optional[str], record_url: Optional[str] = None) -> str:
    """
    Build ExoML using <Play> if audio_url is available, otherwise fallback to <Say>.
    """
    if audio_url:
        return _exoml_play_audio(audio_url, record_url=record_url)
    return _exoml_say(text, record_url=record_url)


# ─── Helper: Exotel REST — place outbound call ────────────────────────────────

async def _exotel_dial_outbound(to_number: str, call_url: str) -> dict:
    """
    Place an outbound call via Exotel REST API.
    Docs: https://developer.exotel.com/api/calls
    """
    if not settings.exotel_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Exotel not configured. Add EXOTEL_ACCOUNT_SID, EXOTEL_API_KEY, "
                "EXOTEL_API_TOKEN, EXOTEL_PHONE_NUMBER to backend/.env"
            ),
        )

    url = (
        f"https://{settings.EXOTEL_SUBDOMAIN}/v1/Accounts/"
        f"{settings.EXOTEL_ACCOUNT_SID}/Calls/connect"
    )
    data = {
        "From": settings.EXOTEL_PHONE_NUMBER,
        "To": to_number,
        "CallerId": settings.EXOTEL_PHONE_NUMBER,
        "Url": call_url,
        "StatusCallback": f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/outbound/status",
        "StatusCallbackContentType": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            data=data,
            auth=(settings.EXOTEL_API_KEY, settings.EXOTEL_API_TOKEN),
        )
        if not resp.is_success:
            raise HTTPException(
                status_code=502,
                detail=f"Exotel call failed ({resp.status_code}): {resp.text}",
            )
        return resp.json()


async def _twilio_dial_outbound(to_number: str, call_url: str) -> dict:
    """
    Place an outbound call via Twilio REST API.
    Docs: https://www.twilio.com/docs/voice/api/call-resource
    """
    if not settings.twilio_configured:
        raise HTTPException(
            status_code=503,
            detail=(
                "Twilio not configured. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
                "and TWILIO_PHONE_NUMBER to backend/.env"
            ),
        )

    # Determine standard or api key SID
    account_sid = os.getenv("TWILIO_ACCOUNT_SID_MAIN") or settings.TWILIO_ACCOUNT_SID
    if account_sid.startswith("SK"):
        main_sid = os.getenv("TWILIO_ACCOUNT_SID_MAIN")
        if not main_sid:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Twilio configuration error: TWILIO_ACCOUNT_SID in .env is an API Key (starts with SK). "
                    "Please also set TWILIO_ACCOUNT_SID_MAIN=AC... (your main Account SID) in backend/.env"
                )
            )
        path_sid = main_sid
    else:
        path_sid = account_sid

    url = f"https://api.twilio.com/2010-04-01/Accounts/{path_sid}/Calls.json"
    data = {
        "From": settings.TWILIO_PHONE_NUMBER,
        "To": to_number,
        "Url": call_url,
        "StatusCallback": f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/twilio/outbound/status",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            data=data,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
        )
        if not resp.is_success:
            raise HTTPException(
                status_code=502,
                detail=f"Twilio call failed ({resp.status_code}): {resp.text}",
            )
        return resp.json()


# ─── Pydantic models ──────────────────────────────────────────────────────────

class TelephonyStatusResponse(BaseModel):
    status: str
    voice_provider: str
    telephony_provider: str
    sarvam_configured: bool
    exotel_configured: bool
    openai_configured: bool
    gemma_configured: bool


class InboundCallPayload(BaseModel):
    """For manual inbound call simulation via API (non-Exotel)."""
    caller: str = Field(..., description="Caller phone number or identifier")
    text: Optional[str] = Field(None, description="Transcribed text from the inbound caller")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded WAV audio for Sarvam STT")
    audio_source: Optional[str] = Field(None, description="Optional audio source token for STT simulation")
    language: Optional[str] = Field(None, description="Preferred caller language: en or ml")
    session_id: Optional[str] = Field(None, description="Existing bot session ID")


class OutboundCallPayload(BaseModel):
    """Payload to initiate a real outbound call via Exotel + Sarvam AI."""
    to_number: str = Field(..., description="Target phone number (e.g. +919876543210)")
    campaign_message: Optional[str] = Field(
        None,
        description="Opening message the bot will speak when the call connects. "
                    "Defaults to the standard greeting from settings."
    )
    language: Optional[str] = Field("en", description="Call language: en or ml")
    agent_name: Optional[str] = Field("Bridgeon Admissions", description="Name of the outbound agent")


class TelephonyCallRecord(BaseModel):
    call_id: str
    caller: str
    status: str
    language: str
    transcript: str
    bot_response: str
    audio_uri: str
    session_id: str
    timestamp: str
    intent: Optional[str] = None
    user_type: Optional[str] = None
    outcome: Optional[str] = None


# ─── Format helper ────────────────────────────────────────────────────────────

def _format_call_record(call: dict) -> dict:
    meta = call.get("metadata") or {}
    return {
        "call_id": call.get("call_id", ""),
        "caller": call.get("caller_number") or "Unknown",
        "status": call.get("outcome", "completed"),
        "language": call.get("language", "en"),
        "transcript": meta.get("transcript", ""),
        "bot_response": meta.get("bot_response", ""),
        "audio_uri": meta.get("audio_uri", ""),
        "session_id": meta.get("session_id", ""),
        "timestamp": call.get("timestamp", ""),
        "intent": meta.get("intent"),
        "user_type": meta.get("user_type"),
        "outcome": call.get("outcome"),
    }


# ─── Status endpoint ──────────────────────────────────────────────────────────

@router.get("/status", response_model=TelephonyStatusResponse, summary="Get telephony + voice status")
async def get_telephony_status():
    voice = get_voice_status()
    return TelephonyStatusResponse(
        status="ok",
        voice_provider=voice.get("voice_provider", "browser"),
        telephony_provider=voice.get("telephony_provider", "stub"),
        sarvam_configured=voice.get("sarvam_configured", False),
        exotel_configured=voice.get("exotel_configured", False),
        openai_configured=voice.get("openai_configured", False),
        gemma_configured=voice.get("gemma_configured", False),
    )


# ─── INBOUND — Manual simulation (text / base64 audio) ───────────────────────

@router.post("/inbound", response_model=TelephonyCallRecord, summary="Simulate or handle an inbound call")
async def simulate_inbound_call(payload: InboundCallPayload, db: Session = Depends(get_db)):
    """
    Handles an inbound call:
    - If audio_base64 is provided → sends to Sarvam AI STT for transcription
    - Otherwise uses payload.text as transcript
    - Runs bot pipeline → generates response
    - Calls Sarvam AI TTS → returns audio_uri with base64 audio
    """
    language = payload.language if payload.language in ("en", "ml") else "en"
    session_id = payload.session_id or f"session-{uuid4().hex[:8]}"
    transcript = payload.text or ""

    # Sarvam AI STT from uploaded audio
    if not transcript and payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
            transcript = await transcribe_audio(audio_bytes, language)
        except Exception:
            pass

    # Stub STT fallback
    if not transcript and payload.audio_source:
        transcript = _STUB.transcribe_audio(payload.audio_source, language)

    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="Provide text, audio_base64 (WAV), or audio_source for the inbound call."
        )

    # Run bot pipeline
    bot_response = await chat(ChatPayload(text=transcript, session_id=session_id, language=language, caller_number=payload.caller), db=db)

    # Sarvam AI TTS
    audio_uri = ""
    tts_audio = await synthesize_speech(bot_response["response_text"], language)
    if tts_audio:
        audio_b64 = base64.b64encode(tts_audio).decode("ascii")
        audio_uri = f"data:audio/wav;base64,{audio_b64}"
    else:
        audio_uri = _STUB.synthesize_speech(bot_response["response_text"], language)

    call_id = f"call-{uuid4().hex[:8]}"
    intent = bot_response.get("intent", "greeting")
    user_type = bot_response.get("user_type", "unknown")
    outcome = "lead_captured" if intent in ("consent_granted", "consent_denied") else (
        "escalated" if intent == "escalated" else "completed"
    )

    call_record = {
        "call_id": call_id,
        "caller_number": payload.caller,
        "duration_seconds": 60.0,
        "language": language,
        "outcome": outcome,
        "call_metadata": {
            "transcript": transcript,
            "bot_response": bot_response["response_text"],
            "audio_uri": audio_uri[:200] if audio_uri.startswith("data:") else audio_uri,
            "session_id": session_id,
            "intent": intent,
            "user_type": user_type,
        },
    }
    logged = log_call(db, call_record)
    record_telephony_call(db, call_record, bot_meta={"intent": intent, "user_type": user_type, "outcome": outcome})

    return {
        "call_id": logged["call_id"],
        "caller": logged["caller_number"],
        "status": "completed",
        "language": logged["language"],
        "transcript": logged["metadata"].get("transcript"),
        "bot_response": logged["metadata"].get("bot_response"),
        "audio_uri": audio_uri,
        "session_id": logged["metadata"].get("session_id"),
        "timestamp": logged["timestamp"],
        "intent": logged["metadata"].get("intent"),
        "user_type": logged["metadata"].get("user_type"),
        "outcome": logged["outcome"],
    }


# ─── INBOUND — Exotel webhook (real call arrives at your number) ───────────────

@router.post(
    "/inbound/webhook",
    response_class=Response,
    summary="Exotel webhook for inbound calls — responds with ExoML"
)
@router.get("/inbound/webhook", response_class=Response, include_in_schema=False)
@router.post("/inbound/webh", response_class=Response, include_in_schema=False)
@router.get("/inbound/webh", response_class=Response, include_in_schema=False)
async def exotel_inbound_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Exotel calls this endpoint when someone dials your virtual number.
    We respond with ExoML to play a TTS greeting (via Sarvam AI).

    Configure this URL in your Exotel App:
    https://your-domain.com/api/v1/telephony/inbound/webhook
    """
    # ── Extract caller info from Exotel POST/GET params ──
    caller = "unknown"
    call_sid = ""
    all_params = {}

    if request.method == "POST":
        try:
            form = await request.form()
            all_params = dict(form)
            caller = (
                form.get("From") or form.get("CallFrom")
                or form.get("from") or form.get("callFrom")
                or "unknown"
            )
            call_sid = form.get("CallSid") or form.get("callSid") or ""
        except Exception as e:
            tlog.error(f"Failed to parse inbound webhook form: {e}")
    else:
        all_params = dict(request.query_params)
        caller = (
            request.query_params.get("From") or request.query_params.get("CallFrom")
            or request.query_params.get("from") or request.query_params.get("callFrom")
            or "unknown"
        )
        call_sid = request.query_params.get("CallSid") or request.query_params.get("callSid") or ""

    tlog.info(f"📞 INBOUND WEBHOOK HIT", caller=caller, call_sid=call_sid, method=request.method)
    tlog.debug(f"All webhook params: {all_params}")

    language = "en"  # Default; can detect from caller region
    session_id = f"exo-{uuid4().hex[:8]}"

    # Get bot greeting
    from app.core.settings_store import get_settings, is_inside_office_hours
    bot_settings = get_settings(db)

    if not is_inside_office_hours(db):
        msg = str(bot_settings.get("after_hours_message_en") or
                  "We are currently outside office hours. Please call back during business hours.")
        tlog.info(f"After hours — hanging up", caller=caller)
        audio_url = await _generate_play_url(msg, language)
        xml = _exoml_hangup(msg, audio_url=audio_url)
    else:
        msg = str(bot_settings.get("greeting_en") or
                  "Hello! Welcome to Bridgeon Skillversity. How can I help you today?")

        # Generate TTS audio for the greeting
        audio_url = await _generate_play_url(msg, language)
        tlog.info(f"Greeting generated", audio_url=bool(audio_url), text_preview=msg[:60])

        # Record caller's response → webhook hits /inbound/recording
        record_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/inbound/recording"
            f"?session_id={session_id}&caller={quote(caller, safe='')}&language={language}"
        )
        tlog.debug(f"Record URL: {record_url}")

        xml = _build_exoml_response(msg, audio_url, record_url=record_url)

    tlog.debug(f"ExoML response:\n{xml}")
    return Response(content=xml, media_type="application/xml")


@router.post(
    "/inbound/recording",
    response_class=Response,
    summary="Exotel callback after caller speaks — processes STT and returns bot response"
)
@router.get("/inbound/recording", response_class=Response, include_in_schema=False)
@router.post("/inbound/rec", response_class=Response, include_in_schema=False)
@router.get("/inbound/rec", response_class=Response, include_in_schema=False)
async def exotel_inbound_recording(
    request: Request,
    session_id: str = "",
    caller: str = "unknown",
    language: str = "en",
    db: Session = Depends(get_db),
):
    """
    Exotel sends the recording URL here after the caller finishes speaking.
    We download the audio, send it to Sarvam AI STT, run the bot, and play the response.
    """
    # ── Extract recording URL from Exotel callback ──
    recording_url = ""
    all_params = {}

    if request.method == "POST":
        try:
            form = await request.form()
            all_params = dict(form)
            recording_url = (
                form.get("RecordingUrl") or form.get("recordingUrl")
                or form.get("RecordUrl") or form.get("recording_url")
                or ""
            )
        except Exception as e:
            tlog.error(f"Failed to parse recording callback form: {e}")
    else:
        all_params = dict(request.query_params)
        recording_url = (
            request.query_params.get("RecordingUrl") or request.query_params.get("recordingUrl")
            or request.query_params.get("RecordUrl") or request.query_params.get("recording_url")
            or ""
        )

    tlog.info(f"🎙️ RECORDING CALLBACK HIT", session_id=session_id, caller=caller, recording_url=recording_url[:100])
    tlog.debug(f"All recording params: {all_params}")

    # ── Download & transcribe the recording ──
    transcript = ""
    if recording_url:
        try:
            tlog.debug(f"Downloading recording from: {recording_url}")
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                # Try with Exotel auth first, then without
                audio_resp = await client.get(
                    recording_url,
                    auth=(settings.EXOTEL_API_KEY, settings.EXOTEL_API_TOKEN),
                )
                if audio_resp.status_code >= 400:
                    tlog.warn(f"Auth download failed ({audio_resp.status_code}), trying without auth")
                    audio_resp = await client.get(recording_url)

                audio_bytes = audio_resp.content
                tlog.debug(f"Downloaded audio: {len(audio_bytes)} bytes, status={audio_resp.status_code}, content-type={audio_resp.headers.get('content-type', 'unknown')}")

                if len(audio_bytes) > 100:  # sanity check — not an error page
                    transcript = await transcribe_audio(audio_bytes, language)
                    tlog.info(f"STT result: '{transcript[:100]}'") if transcript else tlog.warn("STT returned empty transcript")
                else:
                    tlog.warn(f"Audio too small ({len(audio_bytes)} bytes) — likely an error page")

        except Exception as e:
            tlog.error(f"Recording download/STT failed: {e}")
            transcript = ""
    else:
        tlog.warn("No recording URL received from Exotel")

    # ── If no transcript, ask caller to repeat ──
    if not transcript:
        retry_msg = "I'm sorry, I couldn't hear you clearly. Could you please repeat that?"
        retry_audio_url = await _generate_play_url(retry_msg, language)
        retry_record_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/inbound/recording"
            f"?session_id={session_id}&caller={quote(caller, safe='')}&language={language}"
        )
        xml = _build_exoml_response(retry_msg, retry_audio_url, record_url=retry_record_url)
        tlog.debug(f"Retry ExoML:\n{xml}")
        return Response(content=xml, media_type="application/xml")

    # ── Run bot pipeline ──
    tlog.info(f"Running bot pipeline", session_id=session_id, transcript=transcript[:80])
    if session_id not in ["", "unknown"]:
        bot_response = await chat(
            ChatPayload(text=transcript, session_id=session_id, language=language, caller_number=caller), db=db
        )
    else:
        session_id = f"exo-{uuid4().hex[:8]}"
        await chat(ChatPayload(text="__START__", session_id=session_id, language=language, caller_number=caller), db=db)
        bot_response = await chat(
            ChatPayload(text=transcript, session_id=session_id, language=language, caller_number=caller), db=db
        )

    response_text = bot_response.get("response_text", "Thank you for contacting Bridgeon. We look forward to helping you grow with us.")
    bot_state = bot_response.get("state", "unknown")
    tlog.info(f"Bot response", state=bot_state, intent=bot_response.get('intent'), text_preview=response_text[:80])

    updated_language = bot_response.get("language", language)

    # ── Generate TTS for the bot response ──
    response_audio_url = await _generate_play_url(response_text, updated_language)

    # ── Log the call turn ──
    call_id = f"call-{uuid4().hex[:8]}"
    log_call(db, {
        "call_id": call_id,
        "caller_number": caller,
        "duration_seconds": 30.0,
        "language": updated_language,
        "outcome": "in_progress" if bot_state not in ("ended", "escalated") else bot_state,
        "call_metadata": {
            "transcript": transcript,
            "bot_response": response_text,
            "session_id": session_id,
            "intent": bot_response.get("intent"),
            "user_type": bot_response.get("user_type"),
        },
    })

    # ── Build ExoML response ──
    if bot_state in ("ended", "escalated"):
        xml = _exoml_hangup(response_text, audio_url=response_audio_url)
    else:
        # Continue conversation — play response and record next caller input
        next_record_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/inbound/recording"
            f"?session_id={session_id}&caller={quote(caller, safe='')}&language={updated_language}"
        )
        xml = _build_exoml_response(response_text, response_audio_url, record_url=next_record_url)

    tlog.debug(f"Response ExoML:\n{xml}")
    return Response(content=xml, media_type="application/xml")


# ─── Audio Serving — Exotel fetches TTS audio from here ──────────────────────

@router.get(
    "/audio/{audio_id}",
    response_class=Response,
    summary="Serve cached TTS audio for Exotel Play"
)
async def serve_audio(audio_id: str):
    """
    Exotel's <Play> tag fetches audio from this URL.
    Audio is generated by Sarvam AI TTS and cached in memory.
    """
    entry = get_audio(audio_id)
    if not entry:
        tlog.warn(f"Audio not found or expired: {audio_id}")
        raise HTTPException(status_code=404, detail="Audio not found or expired")
    audio_bytes, content_type = entry
    tlog.debug(f"Serving audio {audio_id}: {len(audio_bytes)} bytes")
    return Response(content=audio_bytes, media_type=content_type)


# ─── OUTBOUND — Initiate real call via Exotel ────────────────────────────────

@router.post("/outbound", response_model=TelephonyCallRecord, summary="Initiate a real outbound call via Exotel")
async def initiate_outbound_call(payload: OutboundCallPayload, db: Session = Depends(get_db)):
    """
    Places a real outbound call to the target phone number via Exotel.
    When the call connects, Exotel hits /telephony/outbound/webhook
    which plays the campaign message using Sarvam AI TTS.

    Prerequisites:
    - EXOTEL_ACCOUNT_SID, EXOTEL_API_KEY, EXOTEL_API_TOKEN, EXOTEL_PHONE_NUMBER in .env
    - BACKEND_PUBLIC_URL must be publicly accessible (use ngrok in development)
    - SARVAM_API_KEY for voice synthesis
    """
    language = payload.language if payload.language in ("en", "ml") else "en"
    session_id = f"outbound-{uuid4().hex[:8]}"

    # Build the campaign message
    from app.core.settings_store import get_settings
    bot_settings = get_settings(db)
    campaign_msg = payload.campaign_message or str(
        bot_settings.get("greeting_en") or
        "Hello! This is Bridgeon Skillversity. We're reaching out to share exciting course opportunities. "
        "Are you interested in learning about our programs?"
    )

    call_id = f"outbound-{uuid4().hex[:8]}"
    telephony_provider = settings.telephony_provider
    exotel_call_sid = call_id
    status = "simulated"

    if telephony_provider == "exotel":
        webhook_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/outbound/webhook"
            f"?session_id={session_id}&language={language}"
            f"&message={quote(campaign_msg[:200], safe='')}"
        )
        exotel_resp = await _exotel_dial_outbound(payload.to_number, webhook_url)
        exotel_call_sid = exotel_resp.get("Call", {}).get("Sid") or call_id
        status = "dialing"
    elif telephony_provider == "twilio":
        webhook_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/twilio/outbound/webhook"
            f"?session_id={session_id}&language={language}"
            f"&message={quote(campaign_msg[:200], safe='')}"
        )
        twilio_resp = await _twilio_dial_outbound(payload.to_number, webhook_url)
        exotel_call_sid = twilio_resp.get("sid") or call_id
        status = "dialing"

    # Log the call attempt
    call_record = {
        "call_id": call_id,
        "caller_number": payload.to_number,
        "duration_seconds": 0.0,
        "language": language,
        "outcome": "outbound_initiated",
        "call_metadata": {
            "transcript": "",
            "bot_response": campaign_msg,
            "audio_uri": "",
            "session_id": session_id,
            "intent": "outbound_campaign",
            "user_type": "prospective",
            "exotel_sid": exotel_call_sid,
            "agent_name": payload.agent_name,
            "call_type": "outbound",
        },
    }
    logged = log_call(db, call_record)

    return {
        "call_id": logged["call_id"],
        "caller": payload.to_number,
        "status": status,
        "language": language,
        "transcript": "",
        "bot_response": campaign_msg,
        "audio_uri": "",
        "session_id": session_id,
        "timestamp": logged["timestamp"],
        "intent": "outbound_campaign",
        "user_type": "prospective",
        "outcome": "outbound_initiated",
    }


@router.post(
    "/outbound/webhook",
    response_class=Response,
    summary="Exotel webhook when outbound call connects"
)
async def exotel_outbound_webhook(
    request: Request,
    session_id: str = "",
    language: str = "en",
    message: str = "",
    db: Session = Depends(get_db),
):
    """
    Exotel hits this webhook when the outbound call recipient picks up.
    We play the campaign message and then listen for their response.
    """
    tlog.info(f"📤 OUTBOUND WEBHOOK HIT", session_id=session_id)

    # Get the opening message
    if not message:
        from app.core.settings_store import get_settings
        bot_settings = get_settings(db)
        message = str(
            bot_settings.get("greeting_en") or
            "Hello! This is Bridgeon Skillversity calling. How can we help you today?"
        )

    # Generate TTS audio for outbound greeting
    audio_url = await _generate_play_url(message, language)

    record_url = (
        f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/inbound/recording"
        f"?session_id={session_id}&caller=outbound-recipient&language={language}"
    )
    xml = _build_exoml_response(message, audio_url, record_url=record_url)
    tlog.debug(f"Outbound ExoML:\n{xml}")
    return Response(content=xml, media_type="application/xml")


@router.post("/outbound/status", summary="Exotel call status callback")
async def exotel_outbound_status(request: Request, db: Session = Depends(get_db)):
    """Receives call status updates from Exotel (completed, failed, busy, etc.)."""
    form = await request.form()
    # Log the status for monitoring
    status = form.get("Status") or form.get("CallStatus") or "unknown"
    duration = form.get("Duration") or "0"
    return {"received": True, "status": status, "duration": duration}


@router.post(
    "/twilio/inbound/webhook",
    response_class=Response,
    summary="Twilio webhook for inbound calls — responds with TwiML"
)
async def twilio_inbound_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Twilio calls this endpoint when someone dials your virtual number.
    We respond with TwiML to play the greeting.
    """
    form = await request.form()
    caller = form.get("From") or "unknown"
    language = "en"  # Default language

    session_id = f"tw-{uuid4().hex[:8]}"

    # Get bot greeting
    from app.core.settings_store import get_settings, is_inside_office_hours
    bot_settings = get_settings(db)
    response = VoiceResponse()

    if not is_inside_office_hours(db):
        msg = str(bot_settings.get("after_hours_message_en") or
                  "We are currently outside office hours. Please call back during business hours.")
        response.say(msg)
        response.hangup()
    else:
        msg = str(bot_settings.get("greeting_en") or
                  "Hello! Welcome to Bridgeon Skillversity. How can I help you today?")
        response.say(msg)
        # Record caller's response → webhook hits /twilio/inbound/recording
        record_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/twilio/inbound/recording"
            f"?session_id={session_id}&caller={caller}&language={language}"
        )
        response.record(
            action=record_url,
            max_length=120,
            play_beep=True,
            finish_on_key="#"
        )

    return Response(content=str(response), media_type="application/xml")


@router.post(
    "/twilio/inbound/recording",
    response_class=Response,
    summary="Twilio callback after caller speaks — processes STT and returns bot response"
)
async def twilio_inbound_recording(
    request: Request,
    session_id: str = "",
    caller: str = "unknown",
    language: str = "en",
    db: Session = Depends(get_db),
):
    """
    Twilio sends the recording URL here after the caller finishes speaking.
    We download the audio, send it to STT, run the bot, and play the response.
    """
    form = await request.form()
    recording_url = form.get("RecordingUrl") or ""

    transcript = ""
    if recording_url and settings.twilio_configured:
        try:
            # Download the audio from Twilio
            async with httpx.AsyncClient(timeout=30.0) as client:
                audio_resp = await client.get(
                    recording_url,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
                audio_bytes = audio_resp.content
            transcript = await transcribe_audio(audio_bytes, language)
        except Exception:
            transcript = ""

    response = VoiceResponse()

    if not transcript:
        # If we couldn't transcribe, ask the caller to repeat
        response.say("I'm sorry, I couldn't hear you clearly. Could you please repeat that?")
        next_record_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/twilio/inbound/recording"
            f"?session_id={session_id}&caller={caller}&language={language}"
        )
        response.record(
            action=next_record_url,
            max_length=120,
            play_beep=True,
            finish_on_key="#"
        )
        return Response(content=str(response), media_type="application/xml")

    # Run bot pipeline
    if session_id not in ["", "unknown"]:
        bot_response = await chat(
            ChatPayload(text=transcript, session_id=session_id, language=language, caller_number=caller), db=db
        )
    else:
        session_id = f"tw-{uuid4().hex[:8]}"
        await chat(ChatPayload(text="__START__", session_id=session_id, language=language, caller_number=caller), db=db)
        bot_response = await chat(
            ChatPayload(text=transcript, session_id=session_id, language=language, caller_number=caller), db=db
        )

    response_text = bot_response.get("response_text", "Thank you for contacting Bridgeon. We look forward to helping you grow with us.")
    bot_state = bot_response.get("state", "unknown")

    updated_language = bot_response.get("language", language)

    # Log the call turn
    call_id = f"call-{uuid4().hex[:8]}"
    log_call(db, {
        "call_id": call_id,
        "caller_number": caller,
        "duration_seconds": 30.0,
        "language": updated_language,
        "outcome": "in_progress" if bot_state not in ("ended", "escalated") else bot_state,
        "call_metadata": {
            "transcript": transcript,
            "bot_response": response_text,
            "session_id": session_id,
            "intent": bot_response.get("intent"),
            "user_type": bot_response.get("user_type"),
            "call_type": "inbound",
            "provider": "twilio",
        },
    })

    # Play the response
    response.say(response_text, language="ml-IN" if updated_language == "ml" else "en-IN")

    # If conversation ended, hang up
    if bot_state in ("ended", "escalated"):
        response.hangup()
    else:
        # Continue conversation — record next caller input
        next_record_url = (
            f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/twilio/inbound/recording"
            f"?session_id={session_id}&caller={caller}&language={updated_language}"
        )
        response.record(
            action=next_record_url,
            max_length=120,
            timeout=3,
            play_beep=True,
            finish_on_key="#"
        )

    return Response(content=str(response), media_type="application/xml")


@router.post(
    "/twilio/outbound/webhook",
    response_class=Response,
    summary="Twilio webhook when outbound call connects"
)
async def twilio_outbound_webhook(
    request: Request,
    session_id: str = "",
    language: str = "en",
    message: str = "",
    db: Session = Depends(get_db),
):
    """
    Twilio hits this webhook when the outbound call recipient picks up.
    We play the campaign message and then listen for their response.
    """
    if not message:
        from app.core.settings_store import get_settings
        bot_settings = get_settings(db)
        message = str(
            bot_settings.get("greeting_en") or
            "Hello! This is Bridgeon Skillversity calling. How can we help you today?"
        )

    response = VoiceResponse()
    response.say(message)

    record_url = (
        f"{settings.BACKEND_PUBLIC_URL}/api/v1/telephony/twilio/inbound/recording"
        f"?session_id={session_id}&caller=outbound-recipient&language={language}"
    )
    response.record(
        action=record_url,
        max_length=120,
        timeout=3,
        play_beep=True,
        finish_on_key="#"
    )
    return Response(content=str(response), media_type="application/xml")


@router.post("/twilio/outbound/status", summary="Twilio call status callback")
async def twilio_outbound_status(request: Request):
    """Receives call status updates from Twilio."""
    form = await request.form()
    status = form.get("CallStatus") or "unknown"
    duration = form.get("CallDuration") or "0"
    return {"received": True, "status": status, "duration": duration}


# ─── Call history endpoints ───────────────────────────────────────────────────

@router.get("/calls", response_model=List[TelephonyCallRecord], summary="List all telephony calls")
async def list_telephony_calls(db: Session = Depends(get_db)):
    calls = list_calls(db)
    return [_format_call_record(call) for call in calls]


@router.get("/calls/{call_id}", response_model=TelephonyCallRecord, summary="Get a call record")
async def get_telephony_call(call_id: str, db: Session = Depends(get_db)):
    record = get_call(db, call_id)
    if not record:
        raise HTTPException(status_code=404, detail="Call record not found")
    return _format_call_record(record)
