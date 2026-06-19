"""
Audio cache for serving TTS audio to Exotel via <Play> URLs.

When the bot generates a TTS response, we store the audio bytes in memory
with a unique ID. Exotel's <Play> tag fetches the audio from
  {BACKEND_PUBLIC_URL}/api/v1/telephony/audio/{audio_id}

Audio entries auto-expire after 10 minutes to prevent memory leaks.
"""
import time
import threading
from typing import Optional
from uuid import uuid4

# In-memory audio store: { audio_id: (audio_bytes, content_type, created_at) }
_audio_store: dict = {}
_lock = threading.Lock()

# Audio entries expire after 10 minutes
_TTL_SECONDS = 600


def store_audio(audio_bytes: bytes, content_type: str = "audio/wav") -> str:
    """Store audio bytes and return a unique audio_id."""
    audio_id = uuid4().hex[:12]
    with _lock:
        _audio_store[audio_id] = (audio_bytes, content_type, time.time())
        # Cleanup expired entries
        _cleanup_expired()
    return audio_id


def get_audio(audio_id: str) -> Optional[tuple]:
    """Retrieve (audio_bytes, content_type) or None if expired/missing."""
    with _lock:
        entry = _audio_store.get(audio_id)
        if not entry:
            return None
        audio_bytes, content_type, created_at = entry
        if time.time() - created_at > _TTL_SECONDS:
            del _audio_store[audio_id]
            return None
        return (audio_bytes, content_type)


def _cleanup_expired():
    """Remove expired entries (call within lock)."""
    now = time.time()
    expired = [k for k, (_, _, t) in _audio_store.items() if now - t > _TTL_SECONDS]
    for k in expired:
        del _audio_store[k]
