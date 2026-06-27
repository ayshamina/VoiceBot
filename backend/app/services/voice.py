"""
Voice service layer — Sarvam AI (primary) / OpenAI (fallback).

STT: Sarvam Saaras v3 (supports Malayalam, Hindi, English + more Indian languages)
TTS: Sarvam Bulbul v2 (natural Indian language voices)
LLM: OpenAI GPT-4o-mini (for RAG enhancement)

If no API keys are configured, browser-based speech is used as a fallback.
"""
import base64
import io
import json
from typing import Optional

import httpx

from app.core.config import settings

_SARVAM_BASE = "https://api.sarvam.ai"
_OPENAI_BASE = settings.OPENAI_API_BASE

# Language code mapping: internal code → Sarvam BCP-47 code
_SARVAM_LANG_MAP = {
    "en": "en-IN",
    "ml": "ml-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
}


def _sarvam_headers() -> dict:
    return {"api-subscription-key": settings.SARVAM_API_KEY}


def _openai_headers() -> dict:
    return {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}


def get_voice_status() -> dict:
    """Return which voice backends are active."""
    provider = settings.voice_provider
    telephony = settings.telephony_provider

    llm_type = "local"
    if settings.gemma_configured:
        llm_type = "gemma"
    elif settings.openai_configured:
        llm_type = "openai"

    return {
        "stt": provider,
        "tts": provider,
        "tts_providers": ["sarvam", "elevenlabs", "openai", "browser"] if provider == "browser" else [provider],
        "llm": llm_type,
        "telephony": telephony,
        "sarvam_configured": settings.sarvam_configured,
        "exotel_configured": settings.exotel_configured,
        "openai_configured": settings.openai_configured,
        "twilio_configured": settings.twilio_configured,
        "gemma_configured": settings.gemma_configured,
        "gemma_model": settings.GEMMA_MODEL,
        "voice_provider": provider,
        "telephony_provider": telephony,
        "message": _status_message(),
    }


def _status_message() -> str:
    parts = []
    if settings.sarvam_configured:
        parts.append("Sarvam AI STT/TTS active (Indian languages supported).")
    if settings.gemma_configured:
        parts.append(f"Gemma LLM active (model: {settings.GEMMA_MODEL}).")
    elif settings.openai_configured:
        parts.append("OpenAI STT/TTS/LLM active.")
    if settings.exotel_configured:
        parts.append("Exotel telephony active (real inbound/outbound calls enabled).")
    if not parts:
        parts.append(
            "No AI API keys configured. Add SARVAM_API_KEY to backend/.env for production voice. "
            "Browser speech synthesis used as fallback."
        )
    return " ".join(parts)


# ── Sarvam AI — Speech-to-Text ────────────────────────────────────────────────

async def sarvam_transcribe_audio(audio_bytes: bytes, language: str = "en") -> str:
    """
    Transcribe audio using Sarvam AI Saaras v3.
    Supports: en-IN, ml-IN, hi-IN, ta-IN, te-IN, kn-IN
    Audio format: WAV/MP3/FLAC/OGG, max 30s for sync API.
    """
    if not settings.sarvam_configured or not audio_bytes:
        return ""

    lang_code = _SARVAM_LANG_MAP.get(language, "en-IN")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{_SARVAM_BASE}/speech-to-text",
            headers=_sarvam_headers(),
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            data={
                "model": settings.SARVAM_STT_MODEL,
                "language_code": lang_code,
                "mode": "transcribe",
            },
        )
        response.raise_for_status()
        data = response.json()
        # Sarvam returns {"transcript": "...", ...}
        return data.get("transcript", "").strip()


# ── Sarvam AI — Text-to-Speech ────────────────────────────────────────────────

async def sarvam_synthesize_speech(text: str, language: str = "en") -> Optional[bytes]:
    """
    Synthesize speech using Sarvam AI Bulbul v2.
    Returns raw WAV bytes or None.
    Language codes: en-IN, ml-IN, hi-IN, etc.
    """
    if not settings.sarvam_configured or not text.strip():
        return None

    lang_code = _SARVAM_LANG_MAP.get(language, "en-IN")
    speaker = (
        settings.SARVAM_TTS_SPEAKER_ML if language == "ml"
        else settings.SARVAM_TTS_SPEAKER_EN
    )

    payload = {
        "inputs": [text],
        "target_language_code": lang_code,
        "speaker": speaker,
        "model": settings.SARVAM_TTS_MODEL,
        "pace": 1.0,
        "loudness": 1.5,
        "speech_sample_rate": 22050,
        "enable_preprocessing": True,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{_SARVAM_BASE}/text-to-speech",
            headers={**_sarvam_headers(), "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        # Sarvam returns {"audios": ["<base64-wav>", ...]}
        audios = data.get("audios", [])
        if audios:
            return base64.b64decode(audios[0])
        return None


# ── OpenAI — Speech-to-Text (Whisper fallback) ───────────────────────────────

async def openai_transcribe_audio(audio_bytes: bytes, language: str = "en") -> str:
    """Transcribe audio using OpenAI Whisper. Returns empty string if not configured."""
    if not settings.openai_configured or not audio_bytes:
        return ""

    files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
    data = {"model": "whisper-1"}
    
    # In auto/bilingual mode, do not pass a language hint to Whisper.
    # This enables Whisper's native multilingual auto-detection.
    if language != "auto":
        data["language"] = "ml" if language == "ml" else "en"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{_OPENAI_BASE}/audio/transcriptions",
            headers=_openai_headers(),
            files=files,
            data=data,
        )
        response.raise_for_status()
        return response.json().get("text", "").strip()


# ── OpenAI — Text-to-Speech (fallback) ───────────────────────────────────────

async def openai_synthesize_speech(text: str, language: str = "en") -> Optional[bytes]:
    """Synthesize speech using OpenAI TTS. Returns MP3 bytes or None."""
    if not settings.openai_configured or not text.strip():
        return None

    voice = settings.OPENAI_TTS_VOICE_ML if language == "ml" else settings.OPENAI_TTS_VOICE_EN
    payload = {
        "model": settings.OPENAI_TTS_MODEL,
        "input": text,
        "voice": voice,
        "response_format": "mp3",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{_OPENAI_BASE}/audio/speech",
            headers={**_openai_headers(), "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        return response.content


async def elevenlabs_synthesize_speech(text: str, language: str = "en") -> Optional[bytes]:
    """Synthesize speech using ElevenLabs TTS. Returns MP3 bytes or None."""
    if not settings.elevenlabs_configured or not text.strip():
        return None

    voice_id = "21m00Tcm4TlvDq8ikWAM"
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.content

# ── Unified API — used by all endpoints ──────────────────────────────────────

async def transcribe_audio(audio_bytes: bytes, language: str = "en") -> str:
    """
    Transcribe audio using the best available provider.
    Priority: Sarvam AI → OpenAI Whisper → empty string (browser fallback)
    """
    if settings.sarvam_configured:
        return await sarvam_transcribe_audio(audio_bytes, language)
    if settings.openai_configured:
        return await openai_transcribe_audio(audio_bytes, language)
    return ""


async def synthesize_speech(text: str, language: str = "en") -> Optional[bytes]:
    """
    Synthesize speech using the best available provider.
    Priority: ElevenLabs → Sarvam AI → OpenAI TTS → None (browser fallback)
    """
    if settings.elevenlabs_configured:
        try:
            audio = await elevenlabs_synthesize_speech(text, language)
            if audio:
                return audio
        except Exception as e:
            print(f"[VoiceService] ElevenLabs synthesis failed, trying fallback: {e}")

    if settings.sarvam_configured:
        try:
            audio = await sarvam_synthesize_speech(text, language)
            if audio:
                return audio
        except Exception as e:
            print(f"[VoiceService] Sarvam synthesis failed, trying fallback: {e}")

    if settings.openai_configured:
        try:
            audio = await openai_synthesize_speech(text, language)
            if audio:
                return audio
        except Exception as e:
            print(f"[VoiceService] OpenAI synthesis failed: {e}")

    return None


def normalize_voice_transcript(text: str) -> str:
    """Correct common browser speech-to-text transcription homophones/errors for Bridgeon terms."""
    if not text:
        return text
    
    # Lowercase for uniform replacement
    normalized = text.lower()
    
    # Phrase/word mappings
    replacements = {
        "bridge on": "bridgeon",
        "pigeon": "bridgeon",
        "region": "bridgeon",
        "religion": "bridgeon",
        "bridgeton": "bridgeon",
        "bridgeen": "bridgeon",
        "bridging": "bridgeon",
        
        "marn": "mern",
        "man stack": "mern stack",
        "men stack": "mern stack",
        "mine stack": "mern stack",
        "modern stack": "mern stack",
        
        "flatter": "flutter",
        "floater": "flutter",
        
        "kinra": "kinfra",
        "kin far": "kinfra",
        
        "skill varsity": "skillversity",
        "skill diversity": "skillversity",
        "school varsity": "skillversity",
        
        "kozhikod": "kozhikode",
        "kakanad": "kakkanad",
        "kakkayad": "kakkanad",
    }
    
    for error, correction in replacements.items():
        # Replace whole phrases/words
        normalized = normalized.replace(error, correction)
        
    return normalized


def is_query_relevant_to_bridgeon(query: str) -> bool:
    """Check if the search query is relevant to Bridgeon's courses, services, and admissions."""
    if not query:
        return False
    q_lower = normalize_voice_transcript(query).lower()
    
    # Check if any of these words or substrings are in the query
    relevant_terms = [
        "bridgeon", "skillversity", "course", "fee", "placement", "admission", "syllabus",
        "internship", "training", "project", "duration", "office", "timing", "batch", "class",
        "counselor", "mentor", "student", "learn", "study", "job", "salary", "location", "address",
        "phone", "whatsapp", "brochure", "register", "join", "enroll", "career", "python", "flutter",
        "react", "mern", "science", "design", "ui", "ux", "counseling", "scholarship", "loan", "emi",
        "payment", "pay", "cost", "price", "detail", "information", "qualification", "eligible",
        "eligibility", "require", "requirement", "located", "situated", "office hours", "contact",
        "phone number", "kozhikode", "kinfra", "kakkanad", "calicut", "kochi", "placement cell",
        "software", "developer", "coding", "programming", "web development", "app development",
        "machine learning", "artificial intelligence", "ml", "ai", "javascript", "java", "html",
        "css", "git", "github", "database", "mongodb", "node", "express", "sql", "postgresql",
        "padikkan", "padikkaan", "joli", "jolli", "sambalam", "feesum", "feesu", "admissione",
        "coursine", "കോഴ്സ്", "ഫീസ്", "പ്ലേസ്മെന്റ്", "കൗൺസിലർ", "ബ്രോഷർ", "അഡ്മിഷൻ",
        "ഇന്റേൺഷിപ്പ്", "ട്രെയിനിംഗ്", "ബാച്ച്", "ക്ലാസ്", "ലൊക്കേഷൻ", "വിലാസം", "ഫോൺ",
        "നമ്പർ", "വാട്സാപ്പ്", "രജിസ്റ്റർ", "കരിയർ", "പഠനം", "ജോലി", "ശമ്പളം", "ഓഫീസ്",
        "സമയം", "ബ്രിഡ്ജിയോൺ", "സ്കിൽവേഴ്സിറ്റി", "മലയാളം", "ഇംഗ്ലീഷ്", "മെന്റർ", "പ്രോജക്ട്",
        "ഡെഡ്‌ലൈൻ", "ഷെഡ്യൂൾ", "അഡ്മിഷനെ", "കോഴ്സിന്"
    ]
    
    return any(term in q_lower for term in relevant_terms)


def search_company_info(search_query: str) -> str:
    """Search DuckDuckGo for general queries or falling back to the company."""
    if not is_query_relevant_to_bridgeon(search_query):
        print(f"[RAG/Search] Query '{search_query}' is out of scope. Skipping search.")
        return "No results found on the web."
        
    try:
        from duckduckgo_search import DDGS
        query = search_query.strip()
        
        # Try searching generally first
        results = DDGS().text(query, max_results=3)
        
        # Fallback to company context search if no results and query is specific
        if not results and "bridgeon" not in query.lower() and "skillversity" not in query.lower():
            results = DDGS().text(f"Bridgeon Skillversity {query}", max_results=3)
            
        if not results:
            return "No results found on the web."
        
        snippets = []
        for r in results:
            title = r.get('title')
            body = r.get('body')
            href = r.get('href') or r.get('url') or ""
            source_info = f" (Source: {href})" if href else ""
            snippets.append(f"Title: {title}\nSnippet: {body}{source_info}\n")
        return "\n".join(snippets)
    except Exception as e:
        return f"Error searching the web: {str(e)}"

async def gemma_enhance_rag_answer(query: str, context: str, language: str = "en", chat_history: Optional[list] = None) -> Optional[str]:
    """Use Gemma LLM (local or cloud) to produce a natural answer in Malayalam or English."""
    if not settings.gemma_configured or not settings.GEMMA_API_BASE.strip():
        return None

    lang_label = "Malayalam (use Malayalam script strictly)" if language == "ml" else "English"
    system = (
        f"You are a professional telecaller agent representing Bridgeon, Kinfra, answering customer calls with accurate, up-to-date information about Bridgeon’s services, courses, and policies.\n"
        f"You must talk directly to the customer as a human telecaller. Do NOT analyze the request, do NOT write down your thoughts, do NOT show any step-by-step planning or reasoning, and do NOT list any rules. Output ONLY the spoken response that the customer will hear over the phone. Anything else is a critical failure.\n\n"
        f"Guidelines:\n"
        f"- Tone: Always sound polite, empathetic, professional, confident, and helpful in {lang_label}. Avoid filler words like 'umm' or 'maybe'. Do not use exclamation marks; end statements with periods.\n"
        f"- Strict Scope & Domain Limitation: You MUST ONLY answer questions directly related to Bridgeon, Bridgeon Skillversity, their courses (such as MERN stack, Python, Flutter, Data Science, UI/UX, etc.), placement, admission, fees, or related training details. Under no circumstances should you answer general knowledge, news, weather, cooking, sports, personal questions, or other topics unrelated to Bridgeon. If asked something outside this scope, you must politely decline to answer. For example, if asked in English, say: 'I can only help you with questions about Bridgeon courses. I can connect you to our training counselor for further assistance.' If asked in Malayalam, say: 'എനിക്ക് ബ്രിഡ്ജിയോൺ കോഴ്സുകളെക്കുറിച്ചുള്ള ചോദ്യങ്ങൾക്ക് മാത്രമേ മറുപടി നൽകാൻ സാധിക്കൂ. കൂടുതൽ സഹായത്തിനായി ഞാൻ നിങ്ങളെ കൗൺസിലറുമായി ബന്ധിപ്പിക്കാം.'\n"
        f"- Knowledge Context: Provide clear, confident answers based on the provided Knowledge Context. If the Knowledge Context is garbled, corrupt, empty, or doesn't contain useful information, ignore it completely and answer using your pre-trained general knowledge about Bridgeon Skillversity/courses, or politely say that you can connect them to our training counselor for further assistance. Under NO circumstances should you explain or mention to the caller that the provided context is garbled, corrupt, or missing.\n"
        f"- Bilingual/Conversational Style: When speaking in Malayalam, write English technical terms (like Python, Flutter, MERN, fees, placement, batch, brochure, coordinator, counselor) in Malayalam script (e.g., 'കോഴ്സ്', 'ഫീസ്', 'പ്ലേസ്മെന്റ്', 'കൗൺസിലർ', 'ബ്രോഷർ') instead of using formal, archaic Malayalam translations, to sound like a natural local Kerala telecaller.\n"
        f"- Workflow: Identify the caller’s need quickly and guide them to the next step. Always offer proactive help by asking: 'Would you like me to share the admission form link?' or 'I can connect you to our training coordinator.'\n"
        f"- Output Format: Speak directly to the caller. Do NOT output any internal planning, chain-of-thought, deconstruction of the request, or checklists. Do NOT explain your reasoning. Output ONLY the final, direct spoken response. If answering in Malayalam, use ONLY Malayalam script."
    )
    user = f"Caller question: {query}\n\nKnowledge Context:\n{context}"

    messages = [{"role": "system", "content": system}]
    if chat_history:
        for turn in chat_history[:-1]:
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user})

    headers = {"Content-Type": "application/json"}
    if settings.GEMMA_API_KEY.strip():
        headers["Authorization"] = f"Bearer {settings.GEMMA_API_KEY}"

    payload = {
        "model": settings.GEMMA_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1000
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.GEMMA_API_BASE.strip()}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        resp_json = response.json()
        message = resp_json["choices"][0]["message"]
        content = message.get("content")
        if content:
            return content.strip()
        return None


async def sarvam_enhance_rag_answer(query: str, context: str, language: str = "en", chat_history: Optional[list] = None) -> Optional[str]:
    """Use Sarvam AI LLM (sarvam-30b) to produce a natural answer in Malayalam or English."""
    if not settings.sarvam_configured:
        return None

    lang_label = "Malayalam (use Malayalam script strictly)" if language == "ml" else "English"
    system = (
        f"You are a professional telecaller agent representing Bridgeon, Kinfra, answering customer calls with accurate, up-to-date information about Bridgeon’s services, courses, and policies.\n"
        f"You must talk directly to the customer as a human telecaller. Do NOT analyze the request, do NOT write down your thoughts, do NOT show any step-by-step planning or reasoning, and do NOT list any rules. Output ONLY the spoken response that the customer will hear over the phone. Anything else is a critical failure.\n\n"
        f"Guidelines:\n"
        f"- Tone: Always sound polite, empathetic, professional, confident, and helpful in {lang_label}. Avoid filler words like 'umm' or 'maybe'. Do not use exclamation marks; end statements with periods.\n"
        f"- Strict Scope & Domain Limitation: You MUST ONLY answer questions directly related to Bridgeon, Bridgeon Skillversity, their courses (such as MERN stack, Python, Flutter, Data Science, UI/UX, etc.), placement, admission, fees, or related training details. Under no circumstances should you answer general knowledge, news, weather, cooking, sports, personal questions, or other topics unrelated to Bridgeon. If asked something outside this scope, you must politely decline to answer. For example, if asked in English, say: 'I can only help you with questions about Bridgeon courses. I can connect you to our training counselor for further assistance.' If asked in Malayalam, say: 'എനിക്ക് ബ്രിഡ്ജിയോൺ കോഴ്സുകളെക്കുറിച്ചുള്ള ചോദ്യങ്ങൾക്ക് മാത്രമേ മറുപടി നൽകാൻ സാധിക്കൂ. കൂടുതൽ സഹായത്തിനായി ഞാൻ നിങ്ങളെ കൗൺസിലറുമായി ബന്ധിപ്പിക്കാം.'\n"
        f"- Knowledge Context: Provide clear, confident answers based on the provided Knowledge Context. If the Knowledge Context is garbled, corrupt, empty, or doesn't contain useful information, ignore it completely and answer using your pre-trained general knowledge about Bridgeon Skillversity/courses, or politely say that you can connect them to our training counselor for further assistance. Under NO circumstances should you explain or mention to the caller that the provided context is garbled, corrupt, or missing.\n"
        f"- Bilingual/Conversational Style: When speaking in Malayalam, write English technical terms (like Python, Flutter, MERN, fees, placement, batch, brochure, coordinator, counselor) in Malayalam script (e.g., 'കോഴ്സ്', 'ഫീസ്', 'പ്ലേസ്മെന്റ്', 'കൗൺസിലർ', 'ബ്രോഷർ') instead of using formal, archaic Malayalam translations, to sound like a natural local Kerala telecaller.\n"
        f"- Workflow: Identify the caller’s need quickly and guide them to the next step. Always offer proactive help by asking: 'Would you like me to share the admission form link?' or 'I can connect you to our training coordinator.'\n"
        f"- Output Format: Speak directly to the caller. Do NOT output any internal planning, chain-of-thought, deconstruction of the request, or checklists. Do NOT explain your reasoning. Output ONLY the final, direct spoken response. If answering in Malayalam, use ONLY Malayalam script."
    )
    user = f"Caller question: {query}\n\nKnowledge Context:\n{context}"

    messages = [{"role": "system", "content": system}]
    if chat_history:
        for turn in chat_history[:-1]:
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user})

    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sarvam-30b",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1500
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.sarvam.ai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        resp_json = response.json()
        message = resp_json["choices"][0]["message"]
        content = message.get("content")
        if content:
            return content.strip()
        
        reasoning = message.get("reasoning_content")
        if reasoning:
            return reasoning.strip()
            
        return None


async def enhance_rag_answer(query: str, context: str, language: str = "en", chat_history: Optional[list] = None) -> str:
    """Use OpenAI to produce a natural answer, falling back to web search if needed."""
    if not settings.openai_configured:
        return context

    lang_label = "Malayalam (use Malayalam script strictly)" if language == "ml" else "English"
    system = (
        f"You are a professional telecaller agent representing Bridgeon, Kinfra, answering customer calls with accurate, up-to-date information about Bridgeon’s services, courses, and policies.\n"
        f"You must talk directly to the customer as a human telecaller. Do NOT analyze the request, do NOT write down your thoughts, do NOT show any step-by-step planning or reasoning, and do NOT list any rules. Output ONLY the spoken response that the customer will hear over the phone. Anything else is a critical failure.\n\n"
        f"Guidelines:\n"
        f"- Tone: Always sound polite, empathetic, professional, confident, and helpful in {lang_label}. Avoid filler words like 'umm' or 'maybe'. Do not use exclamation marks; end statements with periods.\n"
        f"- Strict Scope & Domain Limitation: You MUST ONLY answer questions directly related to Bridgeon, Bridgeon Skillversity, their courses (such as MERN stack, Python, Flutter, Data Science, UI/UX, etc.), placement, admission, fees, or related training details. Under no circumstances should you answer general knowledge, news, weather, cooking, sports, personal questions, or other topics unrelated to Bridgeon. If asked something outside this scope, you must politely decline to answer. For example, if asked in English, say: 'I can only help you with questions about Bridgeon courses. I can connect you to our training counselor for further assistance.' If asked in Malayalam, say: 'എനിക്ക് ബ്രിഡ്ജിയോൺ കോഴ്സുകളെക്കുറിച്ചുള്ള ചോദ്യങ്ങൾക്ക് മാത്രമേ മറുപടി നൽകാൻ സാധിക്കൂ. കൂടുതൽ സഹായത്തിനായി ഞാൻ നിങ്ങളെ കൗൺസിലറുമായി ബന്ധിപ്പിക്കാം.'\n"
        f"- Knowledge Context: Provide clear, confident answers based on the provided Knowledge Context. If you need to use the `search_company_info` tool to browse the web for missing details, you may do so only if the search query is related to Bridgeon or its courses. If the Knowledge Context is empty, ignore it and answer using your pre-trained general knowledge about Bridgeon Skillversity/courses, or politely say that you can connect them to our training counselor for further assistance. Under NO circumstances should you explain or mention to the caller that the provided context is garbled, corrupt, or missing.\n"
        f"- Bilingual/Conversational Style: When speaking in Malayalam, write English technical terms (like Python, Flutter, MERN, fees, placement, batch, brochure, coordinator, counselor) in Malayalam script (e.g., 'കോഴ്സ്', 'ഫീസ്', 'പ്ലേസ്മെന്റ്', 'കൗൺസിലർ', 'ബ്രോഷർ') instead of using formal, archaic Malayalam translations, to sound like a natural local Kerala telecaller.\n"
        f"- Workflow: Identify the caller’s need quickly and guide them to the next step. Always offer proactive help by asking: 'Would you like me to share the admission form link?' or 'I can connect you to our training coordinator.'\n"
        f"- Output Format: Speak directly to the caller. Do NOT output any internal planning, chain-of-thought, deconstruction of the request, or checklists. Do NOT explain your reasoning. Output ONLY the final, direct spoken response. If answering in Malayalam, use ONLY Malayalam script."
    )
    user = f"Caller question: {query}\n\nKnowledge Context:\n{context}"

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_company_info",
                "description": "Search the web for information about Bridgeon Skillversity or general coding courses.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "The specific query to search for, e.g., 'React course fee', 'placement reviews'."
                        }
                    },
                    "required": ["search_query"]
                }
            }
        }
    ]

    messages = [{"role": "system", "content": system}]
    if chat_history:
        for turn in chat_history[:-1]:
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user})

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{_OPENAI_BASE}/chat/completions",
            headers={**_openai_headers(), "Content-Type": "application/json"},
            json={
                "model": settings.OPENAI_MODEL,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
                "max_tokens": 400,
                "temperature": 0.3,
            },
        )
        response.raise_for_status()
        resp_data = response.json()
        choice = resp_data["choices"][0]
        message = choice["message"]

        # Check for tool calls
        if message.get("tool_calls"):
            messages.append(message)  # Append assistant's tool call message
            
            for tool_call in message["tool_calls"]:
                if tool_call["function"]["name"] == "search_company_info":
                    args = json.loads(tool_call["function"]["arguments"])
                    search_query = args.get("search_query", query)
                    print(f"[RAG] Executing Web Search for: {search_query}")
                    
                    search_result = search_company_info(search_query)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "content": search_result
                    })
            
            # Send second request with tool results
            response2 = await client.post(
                f"{_OPENAI_BASE}/chat/completions",
                headers={**_openai_headers(), "Content-Type": "application/json"},
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "max_tokens": 400,
                    "temperature": 0.3,
                },
            )
            response2.raise_for_status()
            resp_data2 = response2.json()
            return resp_data2["choices"][0]["message"]["content"].strip()
            
        return message.get("content", "").strip()


def decode_audio_base64(data: str) -> bytes:
    """Decode base64 audio, stripping data-URL prefix if present."""
    if "," in data and data.startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)
