"""
Application settings loaded from environment variables / .env file.
"""
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Always load backend/.env regardless of working directory (fixes StartVoiceBot.bat)
_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_DIR / ".env")


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Bridgeon Voice Call Assistant")
    APP_VERSION: str = os.getenv("APP_VERSION", "5.0.0")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    TELEPHONY_DEBUG: bool = os.getenv("TELEPHONY_DEBUG", "false").lower() == "true"

    # CORS — split comma-separated string into list
    _raw_origins: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://[::1]:5173",
    )
    ALLOWED_ORIGINS: List[str] = [o.strip() for o in _raw_origins.split(",")]

    # Database — default SQLite path is always under backend/
    _default_sqlite = f"sqlite:///{(_BACKEND_DIR / 'voicebot.db').as_posix()}"
    DATABASE_URL: str = os.getenv("DATABASE_URL", _default_sqlite)
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"

    # Admin auth
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "admin_secret_token_change_me_in_production")

    # ── Sarvam AI (Primary: Indian language STT + TTS) ────────────────────────
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    SARVAM_STT_MODEL: str = os.getenv("SARVAM_STT_MODEL", "saaras:v3")
    SARVAM_TTS_MODEL: str = os.getenv("SARVAM_TTS_MODEL", "bulbul:v2")
    SARVAM_TTS_SPEAKER_EN: str = os.getenv("SARVAM_TTS_SPEAKER_EN", "meera")
    SARVAM_TTS_SPEAKER_ML: str = os.getenv("SARVAM_TTS_SPEAKER_ML", "meera")

    # ── Exotel (Real phone calls — Inbound + Outbound) ────────────────────────
    EXOTEL_ACCOUNT_SID: str = os.getenv("EXOTEL_ACCOUNT_SID", "")
    EXOTEL_API_KEY: str = os.getenv("EXOTEL_API_KEY", "")
    EXOTEL_API_TOKEN: str = os.getenv("EXOTEL_API_TOKEN", "")
    EXOTEL_PHONE_NUMBER: str = os.getenv("EXOTEL_PHONE_NUMBER", "")
    EXOTEL_SUBDOMAIN: str = os.getenv("EXOTEL_SUBDOMAIN", "api.in.exotel.com")
    # Public backend URL for Exotel webhooks (set this to your ngrok URL in dev)
    BACKEND_PUBLIC_URL: str = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

    # ── OpenAI (Optional fallback — STT/TTS/LLM) ─────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TTS_MODEL: str = os.getenv("OPENAI_TTS_MODEL", "tts-1")
    OPENAI_TTS_VOICE_ML: str = os.getenv("OPENAI_TTS_VOICE_ML", "shimmer")
    OPENAI_TTS_VOICE_EN: str = os.getenv("OPENAI_TTS_VOICE_EN", "nova")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")

    # Legacy Twilio (still supported if keys present)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    # ── SMTP Email (REQUIRED for Email Notifications) ────────────────────────
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "admissions@bridgeon.in")
    ADMISSIONS_EMAIL: str = os.getenv("ADMISSIONS_EMAIL", "admissions@bridgeon.in")

    @property
    def sarvam_configured(self) -> bool:
        return bool(self.SARVAM_API_KEY.strip())

    @property
    def exotel_configured(self) -> bool:
        return bool(
            self.EXOTEL_ACCOUNT_SID.strip()
            and self.EXOTEL_API_KEY.strip()
            and self.EXOTEL_API_TOKEN.strip()
            and self.EXOTEL_PHONE_NUMBER.strip()
        )

    @property
    def openai_configured(self) -> bool:
        return bool(self.OPENAI_API_KEY.strip())

    # ── Gemma (Native client — optional) ─────────────────────────────────────
    GEMMA_API_KEY: str = os.getenv("GEMMA_API_KEY", "")
    GEMMA_API_BASE: str = os.getenv("GEMMA_API_BASE", "")
    GEMMA_MODEL: str = os.getenv("GEMMA_MODEL", "gemma2")

    @property
    def gemma_configured(self) -> bool:
        return bool(self.GEMMA_API_KEY.strip() or self.GEMMA_API_BASE.strip())

    @property
    def twilio_configured(self) -> bool:
        return bool(
            self.TWILIO_ACCOUNT_SID.strip()
            and self.TWILIO_AUTH_TOKEN.strip()
            and self.TWILIO_PHONE_NUMBER.strip()
        )

    @property
    def elevenlabs_configured(self) -> bool:
        return bool(self.ELEVENLABS_API_KEY.strip())

    @property
    def smtp_configured(self) -> bool:
        return bool(
            self.SMTP_HOST.strip()
            and self.SMTP_USER.strip()
            and self.SMTP_PASSWORD.strip()
        )

    @property
    def voice_provider(self) -> str:
        """Returns the active STT/TTS provider name."""
        if self.elevenlabs_configured:
            return "elevenlabs"
        if self.sarvam_configured:
            return "sarvam"
        if self.openai_configured:
            return "openai"
        return "browser"

    @property
    def telephony_provider(self) -> str:
        """Returns the active telephony provider name."""
        if self.exotel_configured:
            return "exotel"
        if self.twilio_configured:
            return "twilio"
        return "stub"


settings = Settings()
