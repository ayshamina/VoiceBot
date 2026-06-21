"""
Voice API endpoints — STT, TTS, and service status.
Uses OpenAI when OPENAI_API_KEY is set; otherwise returns guidance for browser fallback.
"""
import base64

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.voice import (
    decode_audio_base64,
    get_voice_status,
    synthesize_speech,
    transcribe_audio,
)

router = APIRouter()


class TranscribePayload(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded audio (webm/wav)")
    language: str = Field("en", description="Language code: en or ml")


class SynthesizePayload(BaseModel):
    text: str = Field(..., description="Text to speak")
    language: str = Field("en", description="Language code: en or ml")


class TranscribeResponse(BaseModel):
    transcript: str
    provider: str


class SynthesizeResponse(BaseModel):
    audio_base64: str
    provider: str
    content_type: str = "audio/mpeg"


@router.get("/status", summary="Get voice service configuration")
async def voice_status():
    return get_voice_status()


@router.post("/transcribe", response_model=TranscribeResponse, summary="Speech-to-text")
async def transcribe(payload: TranscribePayload):
    language = payload.language if payload.language in ("en", "ml") else "en"

    try:
        audio_bytes = decode_audio_base64(payload.audio_base64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid audio data: {exc}") from exc

    transcript = await transcribe_audio(audio_bytes, language)
    provider = settings.voice_provider
    if not transcript:
        raise HTTPException(
            status_code=503,
            detail="Server STT unavailable. Set appropriate API keys in backend/.env or use browser voice input.",
        )

    return TranscribeResponse(transcript=transcript, provider=provider)


@router.post("/synthesize", summary="Text-to-speech (returns MP3 or JSON with base64)")
async def synthesize(payload: SynthesizePayload):
    language = payload.language if payload.language in ("en", "ml") else "en"
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    audio = await synthesize_speech(text, language)
    if not audio:
        raise HTTPException(
            status_code=503,
            detail="Server TTS unavailable. Set OPENAI_API_KEY in backend/.env or use browser speech.",
        )

    mime = "audio/wav" if audio.startswith(b"RIFF") else "audio/mpeg"
    return Response(content=audio, media_type=mime)


@router.post("/synthesize/json", response_model=SynthesizeResponse, summary="TTS as base64 JSON")
async def synthesize_json(payload: SynthesizePayload):
    language = payload.language if payload.language in ("en", "ml") else "en"
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    audio = await synthesize_speech(text, language)
    if not audio:
        raise HTTPException(
            status_code=503,
            detail="Server TTS unavailable. Set OPENAI_API_KEY in backend/.env or use browser speech.",
        )

    mime = "audio/wav" if audio.startswith(b"RIFF") else "audio/mpeg"
    provider = "sarvam" if mime == "audio/wav" else settings.voice_provider
    return SynthesizeResponse(
        audio_base64=base64.b64encode(audio).decode("ascii"),
        provider=provider,
        content_type=mime,
    )
