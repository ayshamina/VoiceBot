"""
Telephony service stubs for Phase 7.
Provides a local adapter interface for inbound call simulation, STT, and TTS.
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import uuid4


class STTService(ABC):
    @abstractmethod
    def transcribe(self, audio_source: str, language: str) -> str:
        raise NotImplementedError


class TTSService(ABC):
    @abstractmethod
    def synthesize(self, text: str, language: str) -> str:
        raise NotImplementedError


class StubSTTService(STTService):
    def transcribe(self, audio_source: str, language: str) -> str:
        # In a real system, audio_source would be audio content or URI.
        return f"[stub transcription in {language}]"


class StubTTSService(TTSService):
    def synthesize(self, text: str, language: str) -> str:
        return f"stub-audio://{language}/{uuid4().hex}"


class TelephonyAdapter(ABC):
    def __init__(self, stt: STTService, tts: TTSService) -> None:
        self.stt = stt
        self.tts = tts

    def transcribe_audio(self, audio_source: str, language: str) -> str:
        return self.stt.transcribe(audio_source, language)

    def synthesize_speech(self, text: str, language: str) -> str:
        return self.tts.synthesize(text, language)


class StubTelephonyAdapter(TelephonyAdapter):
    def __init__(self) -> None:
        super().__init__(stt=StubSTTService(), tts=StubTTSService())

    def simulate_inbound(self, caller: str, text: str, language: str, audio_source: Optional[str] = None) -> dict:
        if audio_source and not text:
            transcript = self.transcribe_audio(audio_source, language)
        else:
            transcript = text

        response_audio = self.synthesize_speech(transcript, language)
        return {
            "caller": caller,
            "language": language,
            "transcript": transcript,
            "audio_uri": response_audio,
        }
