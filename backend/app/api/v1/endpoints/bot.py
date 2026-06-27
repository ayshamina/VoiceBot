"""
Bot conversational pipeline endpoints (Phase 3 Simulator Engine)
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.api.v1.endpoints import knowledge, leads
from app.core.database import get_db
from app.core.metrics import record_bot_turn
from app.core.models import BotSession, Lead, Call
from app.core.rag import retrieve_grounded_answer_async
from app.core.settings_store import get_settings, is_inside_office_hours, record_knowledge_gap


router = APIRouter()


class ChatPayload(BaseModel):
    text: str
    session_id: str
    language: Optional[str] = None
    caller_number: Optional[str] = None


class ResetPayload(BaseModel):
    session_id: str


def _get_initial_session() -> Dict[str, Any]:
    return {
        "state": "greeting",
        "user_type": "unknown",
        "lead_data": {"name": None, "phone": None, "course": None, "language": "en"},
        "consent_whatsapp": None,
        "lead_saved": False,
        "language": "en",   # Always start fresh as English; overridden by language selector
        "unclear_attempts": 0,
        "chat_history": [],  # Conversational memory for human-like dialogue
    }


async def _resolve_language_llm(raw_text: str, current_lang: str) -> Optional[str]:
    from app.core.config import settings
    if not settings.openai_configured and not settings.gemma_configured:
        return None

    text_stripped = raw_text.strip()
    if not text_stripped or text_stripped == "__START__" or len(text_stripped.split()) < 2:
        return None

    if bool(re.search(r"[\u0d00-\u0d7f]", text_stripped)):
        return "ml"

    system_prompt = (
        "You are a language detection assistant.\n"
        "Analyze the following transcribed text from a student phone call.\n"
        "Determine whether the speaker is speaking in English or Malayalam (including Malayalam written in Malayalam script, transliterated Malayalam, or Manglish using English alphabet).\n"
        "Respond with ONLY \"en\" (for English) or \"ml\" (for Malayalam). Do not output any other text or explanation.\n"
        f"If the text is neutral (e.g., simple greeting, hello, yes, ok, no) and could be either, default to: {current_lang}"
    )

    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            if settings.gemma_configured:
                url = f"{settings.GEMMA_API_BASE.strip()}/chat/completions"
                headers = {"Content-Type": "application/json"}
                if settings.GEMMA_API_KEY.strip():
                    headers["Authorization"] = f"Bearer {settings.GEMMA_API_KEY}"
                payload = {
                    "model": settings.GEMMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User text: \"{text_stripped}\""}
                    ],
                    "max_tokens": 10,
                    "temperature": 0.0,
                }
            else:
                url = f"{settings.OPENAI_API_BASE}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User text: \"{text_stripped}\""}
                    ],
                    "max_tokens": 10,
                    "temperature": 0.0,
                }

            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            res_json = response.json()
            detected = res_json["choices"][0]["message"]["content"].strip().lower()
            if detected in ("en", "ml"):
                return detected
    except Exception as e:
        print(f"[LanguageDetect] LLM detection failed: {e}")
    return None


# Smarter list and suffix definitions for local fast-path language detection
ML_TRANSLITERATED_WORDS = {
    # Pronouns & Basics
    "njan", "njann", "njangal", "njangalude", "ningal", "ningalude", "enikku", "enikk", "enik",
    "nammal", "nammalude", "nte", "ente", "sukhamaano", "sukhamaanoo", "sukhamano",
    "nandi", "athe", "alla", "sari", "sheriyaanu", "sheriyanu", "pinne", "pakshe", 
    "matte", "engil", "enthu", "aano", "aanu", "alle", "yo", "uoo", "undo", "illa", 
    "illaa", "und", "undd", "unde", "aam", "namaskaram", "namaskaaram", "swagatham", "swaagatham",
    "ethra", "ethrayaanu", "ethrayanu", "ethraya", "evide", "evideya", "evideyaanu", "evideyanu",
    "eppo", "eppol", "eppozha", "eppozhaan", "eppozhanu", "engane", "enganeyaanu",
    "enth", "entha", "enthaanu", "enthanu", "enthann", "aara", "aaraan", "aaraanu",
    
    # Common Malayalam verbs/nouns transliterated
    "samsarikkan", "samsarikkoo", "samsarikkam", "samsarikaam", "samsarikk", "samsarikkatte",
    "samsarikkaamo", "parayoo", "parayu", "parayam", "parayaam", "parayamo", "parayaamo", 
    "parayatte", "para", "ariyan", "ariyaan", "ariyam", "ariyaam", "ariyanam", "ariyaanam", 
    "ariyamo", "ariyilla", "chodikkan", "chodikkaan", "chodikkam", "chodikkaam", "chodikkanam", 
    "chodikkatte", "chodikkaamo", "choyikkan", "choyikkaan", "choyikkam", "choyikkaam",
    "choyikkanam", "choyikkaamo", "nokkam", "nokaam", "nokkan", "nookkan", "nokkanam", 
    "nokkatte", "nalkam", "nalkamo", "nalkaamo", "tharumo", "tharaamo", "tharu", "cheyyan", 
    "cheyyaan", "cheyyamo", "cheyyaamo", "cheyyo", "cheyyatte", "cheyyam", "cheyyaam",
    "patto", "pattumo", "pattum", "pattilla", "nadakkum", "nadakkilla", "nadakkoola", 
    "nadakoolla", "padikkan", "padikkaan", "padikkanam", "padikkaanam", "manassilayi", 
    "manasilayi", "manassilayilla", "manasilayilla", "joli", "jolli", "jolikari", 
    "sambalam", "mathi", "aakku", "thirinju", "manസ്സിലായി", "pattilla", "nannayi", 
    "valare", "ithu", "athu", "ethu", "ithanu", "ithaanu", "athanu", "athaanu",
    "venam", "venda", "venamennund", "thalparyam", "thalparyamund", "thalparyamilla",
    "keralathil", "kozhikode", "kinfra", "kakkanad", "malayalam", "malayalathil",
    "english", "englishil"
}

ML_SUFFIXES = [
    "inte", "aano", "alle", "ikkaan", "ikkan", "ikkoo", "ikkaam", "unnu", "unno", 
    "undo", "illa", "ude", "il", "odu", "athu", "ethu", "ithu", "aanu", "anu",
    "aamo", "aam", "ukayaanu", "ukayanu", "engil", "ayirunnu", "aayirunnu", 
    "ayirunno", "aayirunno", "allallo", "allalloo", "uka", "tharaam", "tharam", 
    "tharoo", "kodukkaam", "kodukkam", "kodukkoo"
]

EN_INDICATOR_WORDS = {
    "what", "why", "how", "where", "when", "who", "which", "is", "are", "do", "does", 
    "did", "can", "could", "should", "would", "please", "course", "courses", "fees", 
    "fee", "placement", "placements", "admission", "admissions", "syllabus", "internship", 
    "internships", "training", "project", "projects", "duration", "office", "hours", 
    "time", "timing", "timings", "class", "classes", "batch", "batches", "counselor", 
    "mentor", "student", "learn", "study", "job", "salary", "work", "location", "address", 
    "phone", "number", "call", "callback", "whatsapp", "brochure", "register", "join", 
    "enroll", "thank", "thanks", "career", "development", "program", "stack", "python", 
    "flutter", "react", "mern", "science", "design", "ui", "ux", "counseling", "scholarship", 
    "loan", "emi", "payment", "pay", "cost", "price", "about", "detail", "details", "information",
    "any", "some", "many", "much", "more", "less", "qualification", "eligibility", "eligible",
    "require", "required", "requirements", "located", "situated", "whereis"
}

NEUTRAL_WORDS = {
    "hello", "hi", "yes", "no", "ok", "okay", "hallo", "hey", "yep", "yeah", "sure", 
    "namaskaram", "namaskaaram", "ഹലോ", "നമസ്കാരം", "അതെ", "ശരി"
}


async def _resolve_language(session: Dict[str, Any], preferred: Optional[str], raw_text: str, db: Session) -> str:
    text_lower = raw_text.lower().strip()
    
    # Short-circuit system startup commands to avoid heuristics/LLM overhead
    if text_lower in ("__start__", "__start__"):
        if "language" not in session:
            session["language"] = preferred if preferred in ("en", "ml") else "en"
        return session["language"]

    words = set(re.findall(r"\w+", text_lower))

    if not words:
        if "language" not in session:
            session["language"] = preferred if preferred in ("en", "ml") else "en"
        return session["language"]

    # 1. Check for explicit bilingual switch commands (English, Malayalam script, and Malayalam transliterated)
    ml_switch_triggers = [
        "speak in malayalam", "talk in malayalam", "switch to malayalam", "change to malayalam",
        "speak malayalam", "talk malayalam", "malayalathil samsarikkoo", "malayalam samsarikkoo",
        "malayalam mathi", "malayalathil aakku", "malayalathil parayoo", "malayalam parayoo",
        "malayalathil samsarikkaamo", "malayalam samsarikkaamo", "malayalathil parayaamo",
        "മലയാളത്തിൽ സംസാരിക്കൂ", "മലയാളം സംസാരിക്കൂ", "മലയാളം മതി", "മലയാളത്തിൽ ആക്കൂ",
        "മലയാളത്തിൽ പറയൂ", "മലയാളത്തിൽ സംസാരിക്കാമോ", "മലയാളത്തിൽ സംസാരിക്കുക"
    ]

    en_switch_triggers = [
        "speak in english", "talk in english", "switch to english", "change to english",
        "speak english", "talk english", "englishil samsarikkoo", "english samsarikkoo",
        "english mathi", "englishil aakku", "englishil parayoo", "english parayoo",
        "englishil samsarikkaamo", "english samsarikkaamo", "englishil parayaamo",
        "ഇംഗ്ലീഷിൽ സംസാരിക്കൂ", "ഇംഗ്ലീഷ് സംസാരിക്കൂ", "ഇംഗ്ലീഷ് മതി", "ഇംഗ്ലീഷിൽ ആക്കൂ",
        "ഇംഗ്ലീഷിൽ പറയൂ", "ഇംഗ്ലീഷിൽ സംസാരിക്കാമോ", "ഇംഗ്ലീഷ് സംസാരിക്കുക"
    ]

    # Check for direct matches in the text
    for trigger in ml_switch_triggers:
        if trigger in text_lower:
            session["language"] = "ml"
            return "ml"

    for trigger in en_switch_triggers:
        if trigger in text_lower:
            session["language"] = "en"
            return "en"

    # 2. Check for Malayalam Unicode script (character-based detection - 100% confident)
    if _contains_malayalam(raw_text):
        session["language"] = "ml"
        return "ml"

    # 3. Check for purely neutral words (keep current language, no switch)
    if words.issubset(NEUTRAL_WORDS):
        if "language" not in session:
            session["language"] = preferred if preferred in ("en", "ml") else "en"
        return session["language"]

    # 3.1 Keep active language for short technical answers or nouns (like course names or numbers)
    course_terms = {"mern", "stack", "python", "flutter", "react", "science", "design", "ui", "ux", "java"}
    if len(words) <= 2 and (words.issubset(course_terms.union(NEUTRAL_WORDS)) or all(w.isdigit() for w in words)):
        if "language" in session:
            return session["language"]

    # 4. Smart Local Heuristics (Zero Delay)
    ml_score = 0.0
    en_score = 0.0

    # 4.1 Check exact transliterated Malayalam words
    ml_matches = words.intersection(ML_TRANSLITERATED_WORDS)
    ml_score += len(ml_matches) * 2.0

    # 4.2 Check grammatical suffixes
    has_ml_suffix = False
    for word in words:
        if len(word) > 4:
            if word.endswith("nte") and word not in ("ante", "monte", "forte", "pointe", "route", "site"):
                has_ml_suffix = True
                ml_score += 1.5
            else:
                for suffix in ML_SUFFIXES:
                    if word.endswith(suffix):
                        has_ml_suffix = True
                        ml_score += 1.5
                        break

    # 4.3 Check English indicator words (penalizing borrowed nouns in Manglish)
    en_matches = words.intersection(EN_INDICATOR_WORDS)
    borrowed_nouns = {
        "job", "placement", "fees", "fee", "course", "courses", "batch", "batches", 
        "class", "classes", "whatsapp", "brochure", "timing", "timings", "mern", 
        "stack", "python", "flutter", "react", "design", "development", "admissions",
        "counseling", "syllabus", "duration", "salary", "package", "internship", "projects", "project"
    }
    for match in en_matches:
        if match in borrowed_nouns:
            en_score += 0.5  # Low score weight
        else:
            en_score += 1.5  # High score weight for English-only structure/question words

    # 4.4 Score-based decision
    if ml_score > 0 or has_ml_suffix:
        # Malayalam structure/grammar wins
        session["language"] = "ml"
        return "ml"
    elif en_score > 0:
        # Clearly English query
        session["language"] = "en"
        return "en"

    # 5. Fallback: Default to current active language to save network latency (approx 1-2s).
    # Since local heuristics are robust, we bypass the LLM lookup to maximize voice efficiency.
    current_lang = session.get("language") or preferred or "en"
    if "language" not in session:
        session["language"] = current_lang if current_lang in ("en", "ml") else "en"

    return session["language"]



def _greeting_text(language: str, db: Session) -> str:
    settings = get_settings(db)
    if language == "ml":
        return str(settings.get("greeting_ml") or settings.get("greeting_en") or "")
    return str(settings.get("greeting_en") or settings.get("greeting_ml") or "")


def _after_hours_text(language: str, db: Session) -> str:
    settings = get_settings(db)
    if language == "ml":
        return str(settings.get("after_hours_message_ml") or settings.get("after_hours_message_en") or "")
    return str(settings.get("after_hours_message_en") or settings.get("after_hours_message_ml") or "")


def _escalation_message(session: Dict[str, Any], db: Session) -> str:
    settings = get_settings(db)
    number = settings.get("escalation_number", "our support team")
    if session.get("language") == "ml":
        return (
            f"ക്ഷമിക്കണം, എനിക്ക് മനസ്സിലായില്ല. "
            f"കൂടുതൽ സഹായത്തിനായി ഞാൻ നിങ്ങളെ ശരിയായ വിഭാഗവുമായി ബന്ധിപ്പിക്കാം. ദയവായി {number} എന്ന നമ്പറിൽ കാത്തിരിക്കുക."
        )
    return (
        f"I'm sorry, I'm having trouble understanding. "
        f"I’ll connect you to the right department for further assistance. Please hold while we transfer you to {number}."
    )


def _outcome_for_intent(intent: str) -> str:
    if intent in ("consent_granted", "consent_denied"):
        return "lead_captured"
    if intent == "escalated":
        return "escalated"
    if intent in (
        "faq_response",
        "rag_response",
        "farewell",
        "check_schedule",
        "check_deadline",
        "contact_mentor",
        "placement_queries",
        "course_info",
        "send_materials",
        "request_phone_for_materials",
    ):
        return "resolved"
    return "in_progress"


def _finalize(session: Dict[str, Any], session_id: str, result: Dict[str, Any], db: Session) -> Dict[str, Any]:
    settings = get_settings(db)
    intent = str(result.get("intent", "unknown"))
    outcome = _outcome_for_intent(intent)
    record_bot_turn(
        db=db,
        session_id=session_id,
        intent=intent,
        user_type=str(result.get("user_type", "unknown")),
        language=session.get("language", "en"),
        outcome=outcome,
        escalated=intent == "escalated",
    )
    result["language"] = session.get("language", "en")
    result["engine_mode"] = settings.get("engine_mode", "paid")
    return result


def _contains_malayalam(text: str) -> bool:
    return bool(re.search(r"[\u0d00-\u0d7f]", text))





def _detect_emotion_and_tone(text: str) -> str:
    text_lower = text.lower()
    frustrated_keywords = [
        "frustrated", "worst", "garbage", "trash", "useless", "stupid", "dumb", 
        "annoyed", "angry", "hate", "terrible", "bad", "operator", "human", 
        "counselor", "transfer", "crap", "waste of time", "unhappy", "irritated",
        "ദേഷ്യം", "മോശം", "കൊള്ളില്ല", "മടുപ്പ്", "കഷ്ടം"
    ]
    confused_keywords = [
        "confused", "don't understand", "not understanding", "what?", "how?", 
        "explain", "unclear", "doubt", "lost", "perplexed", "puzzled",
        "മനസ്സിലാകുന്നില്ല", "എന്താണ്", "സംശയം"
    ]
    excited_keywords = [
        "excited", "happy", "awesome", "great", "cool", "wonderful", "perfect", 
        "good", "love", "amazing", "excellent", "superb",
        "സന്തോഷം", "കൊള്ളാം", "സൂപ്പർ", "അടിപൊളി"
    ]
    
    if any(k in text_lower for k in frustrated_keywords):
        return "frustrated"
    if any(k in text_lower for k in confused_keywords):
        return "confused"
    if any(k in text_lower for k in excited_keywords):
        return "excited"
    return "neutral"


def _apply_emotion_prefix(response_text: str, emotion: str, language: str) -> str:
    if emotion == "neutral" or not response_text:
        return response_text
    
    prefixes = {
        "en": {
            "frustrated": "I understand this is frustrating. Let me help clarify: ",
            "confused": "No worries! It's completely normal to feel confused. Let me explain: ",
            "excited": "That's fantastic! I'm glad to hear that. ",
        },
        "ml": {
            "frustrated": "നിങ്ങൾക്ക് ബുദ്ധിമുട്ടുണ്ടായതിൽ ഖേദിക്കുന്നു. ഞാൻ ഇത് വിശദീകരിക്കാം: ",
            "confused": "വിഷമിക്കേണ്ട, സംശയങ്ങൾ ഉണ്ടാകുന്നത് സാധാരണമാണ്. ഞാൻ ലളിതമായി പറയാം: ",
            "excited": "വളരെ സന്തോഷം! ",
        }
    }
    
    lang = "ml" if language == "ml" else "en"
    prefix = prefixes[lang].get(emotion, "")
    
    if prefix and not response_text.startswith(prefix):
        return f"{prefix}{response_text}"
    return response_text


def _initialize_long_term_memory(session: Dict[str, Any], db: Session) -> None:
    caller_num = session.get("caller_number")
    if not caller_num or caller_num in ("unknown", "Web Browser Client"):
        session["long_term_memory"] = {}
        return

    try:
        from app.api.v1.endpoints.leads import _normalize_phone
        clean_phone = _normalize_phone(caller_num)
    except Exception:
        clean_phone = "".join(filter(str.isdigit, caller_num))

    lead = db.query(Lead).filter(Lead.phone == clean_phone).first()
    if lead:
        session["long_term_memory"] = {
            "name": lead.name,
            "course": lead.course,
            "is_lead": True,
            "last_interaction": "lead_capture"
        }
        session["lead_data"]["name"] = lead.name
        session["lead_data"]["phone"] = lead.phone
        session["lead_data"]["course"] = lead.course
        return

    past_call = db.query(Call).filter(Call.caller_number == caller_num).order_by(Call.timestamp.desc()).first()
    if past_call and past_call.call_metadata:
        meta = past_call.call_metadata
        course = meta.get("course") or meta.get("intent") or "our programs"
        session["long_term_memory"] = {
            "name": "there",
            "course": course,
            "is_lead": False,
            "last_interaction": "past_call"
        }
        return

    session["long_term_memory"] = {}


def _transition_to_next_capture_state(session: Dict[str, Any]) -> Dict[str, Any]:
    lead_data = session.get("lead_data", {})
    lang = session.get("language", "en")

    if not lead_data.get("name"):
        session["state"] = "lead_capture_name"
        msg = "തീർച്ചയായും, നിങ്ങളെ സഹായിക്കുന്നതിൽ എനിക്ക് സന്തോഷമേയുള്ളൂ. ആദ്യം നിങ്ങളുടെ പേര് ഒന്ന് പറയാമോ?" if lang == "ml" else "Of course! I would be delighted to help you. May I know your name first, please?"
        return {
            "response_text": msg,
            "state": "lead_capture_name",
            "user_type": "prospective",
            "intent": "request_callback"
        }
    elif not lead_data.get("phone"):
        session["state"] = "lead_capture_phone"
        name = lead_data['name']
        if lang == "ml":
            msg = f"{name}, ഞങ്ങളുടെ അഡ്മിഷൻ ടീം ബന്ധപ്പെടാൻ ഏറ്റവും നല്ല ഫോൺ നമ്പർ ഏതാണ്?"
        else:
            msg = f"Nice to meet you, {name}! What is the best phone number for our admissions team to contact you?"
        return {
            "response_text": msg,
            "state": "lead_capture_phone",
            "user_type": "prospective",
            "intent": "capture_name"
        }
    elif not lead_data.get("course"):
        session["state"] = "lead_capture_course"
        if lang == "ml":
            msg = "ഏത് കോഴ്‌സ് ആണ് നിങ്ങൾക്ക് ഏറ്റവും കൂടുതൽ താൽപ്പര്യം? (MERN Stack, Python, Flutter, Data Science, UI/UX...)"
        else:
            msg = "Got it! And finally, which course or training track are you most interested in? (MERN Stack, Python, Flutter, Data Science, UI/UX...)"
        return {
            "response_text": msg,
            "state": "lead_capture_course",
            "user_type": "prospective",
            "intent": "capture_phone"
        }
    else:
        session["state"] = "consent_whatsapp"
        if lang == "ml":
            msg = "നിങ്ങളുടെ വിവരങ്ങൾ സേവ് ചെയ്തു. ഒരു കൗൺസലർ ഉടൻ ബന്ധപ്പെടും. കോഴ്‌സ് ബ്രോഷർ WhatsApp-ൽ അയക്കട്ടെയോ?"
        else:
            msg = "Excellent! I have saved your details. A counselor will contact you. Shall I also send the course brochure to your WhatsApp?"
        return {
            "response_text": msg,
            "state": "consent_whatsapp",
            "user_type": "prospective",
            "intent": "capture_course"
        }


async def _check_intent_switch(raw_text: str, text: str, session: Dict[str, Any], db: Session) -> Optional[Dict[str, Any]]:
    scripted_states = ["lead_capture_name", "lead_capture_phone", "lead_capture_course", "consent_whatsapp"]
    if session.get("state") not in scripted_states:
        return None

    # Exclude basic answers from intent switching to avoid false positives
    if len(text.split()) <= 2 and not any(k in text for k in ["fee", "cost", "placement", "job", "salary", "schedule", "deadline", "course", "program", "class", "timings"]):
        # It's likely just the caller's name or direct answer
        return None

    # Always use retrieve_grounded_answer_async which queries both vector store and database
    rag_answer = await retrieve_grounded_answer_async(raw_text, db, language=session.get("language", "en"), chat_history=session.get("chat_history"))
    if rag_answer:
        return {
            "answer": rag_answer,
            "intent": "rag_response"
        }
            
    return None


def get_bot_session(session_id: str, db: Session) -> Dict[str, Any]:
    """Retrieve session state from database, or create a new one if not exists."""
    session_obj = db.query(BotSession).filter(BotSession.session_id == session_id).first()
    if not session_obj:
        initial_data = _get_initial_session()
        session_obj = BotSession(session_id=session_id, session_data=initial_data)
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)
    return session_obj.session_data


def save_bot_session(session_id: str, session_data: Dict[str, Any], db: Session):
    """Save session state to database."""
    session_obj = db.query(BotSession).filter(BotSession.session_id == session_id).first()
    if session_obj:
        session_obj.session_data = dict(session_data)
        flag_modified(session_obj, "session_data")
        session_obj.updated_at = datetime.now(timezone.utc)
        db.commit()


@router.post("/chat", summary="Process text through conversational engine")
async def chat(payload: ChatPayload, db: Session = Depends(get_db)):
    """
    Simulates speech recognition input, feeds it to the bot pipeline state machine,
    and returns intent, state status, and the spoken/written response.
    """
    session_id = payload.session_id
    from app.services.voice import normalize_voice_transcript
    raw_text = normalize_voice_transcript(payload.text.strip())
    text = raw_text.lower()

    session = get_bot_session(session_id, db)
    if "chat_history" not in session:
        session["chat_history"] = []

    if payload.caller_number:
        session["caller_number"] = payload.caller_number
        
    await _resolve_language(session, payload.language, raw_text, db)
    
    if "long_term_memory" not in session and session.get("caller_number"):
        _initialize_long_term_memory(session, db)
        
    # Record user turn in chat history
    if raw_text not in ("__START__", "__start__"):
        session["chat_history"].append({"role": "user", "content": raw_text})
        
    result = await _handle_chat_turn(session, raw_text, text, db)
    
    emotion = _detect_emotion_and_tone(raw_text)
    result["response_text"] = _apply_emotion_prefix(result.get("response_text", ""), emotion, session.get("language", "en"))
    result["emotion"] = emotion
    
    # Record assistant turn in chat history
    if result.get("response_text"):
        session["chat_history"].append({"role": "assistant", "content": result["response_text"]})
        session["chat_history"] = session["chat_history"][-20:]  # Bound history size
        
    res = _finalize(session, session_id, result, db)
    save_bot_session(session_id, session, db)
    return res


async def _handle_chat_turn(session: Dict[str, Any], raw_text: str, text: str, db: Session) -> Dict[str, Any]:
    state = session["state"]

    # 1. Trigger Initial Call Setup
    if raw_text == "__START__" or text == "__start__" or not state:
        # Language was already set by _resolve_language (which runs before this function)
        language = session.get("language", "en")
        if not is_inside_office_hours(db):
            session["state"] = "after_hours"
            return {
                "response_text": _after_hours_text(language, db),
                "state": "after_hours",
                "user_type": "unknown",
                "intent": "after_hours",
            }

        # Check long term memory for returning greeting
        ltm = session.get("long_term_memory")
        if ltm and ltm.get("name"):
            name = ltm["name"]
            course = ltm.get("course") or "our programs"
            
            # Greet based on user_type
            if session.get("user_type") == "student":
                session["state"] = "student_faq"
                if language == "ml":
                    msg = f"വീണ്ടും സ്വാഗതം, {name}! നിങ്ങളുടെ {course} പഠനം എങ്ങനെയുണ്ട്? ഇന്ന് ബാച്ച് ഷെഡ്യൂൾ അല്ലെങ്കിൽ പ്രോജക്ട് ഡെഡ്‌ലൈൻ എന്നിവ നോക്കണോ?"
                else:
                    msg = f"Welcome back, {name}! Hope your {course} training is going well. I can help you check weekly batch schedules, project deadlines, or notify your mentor. What would you like to check today?"
                return {
                    "response_text": msg,
                    "state": "student_faq",
                    "user_type": "student",
                    "intent": "student_check_in",
                }
            else:
                # Prospective student
                session["state"] = "explore_courses"
                session["user_type"] = "prospective"
                if language == "ml":
                    msg = f"വീണ്ടും സ്വാഗതം, {name}! കഴിഞ്ഞ തവണ നിങ്ങൾ {course} കോഴ്‌സിനെക്കുറിച്ചാണ് അന്വേഷിച്ചത്. അതിനെക്കുറിച്ച് കൂടുതൽ അറിയണോ, അതോ മറ്റ് ചോദ്യങ്ങളുണ്ടോ?"
                else:
                    msg = f"Welcome back, {name}! Last time you inquired about our {course} course. Would you like to continue exploring that, or do you have other questions today?"
                return {
                    "response_text": msg,
                    "state": "explore_courses",
                    "user_type": "prospective",
                    "intent": "explore_courses",
                }

        session["state"] = "greeting"
        return {
            "response_text": _greeting_text(language, db),
            "state": "greeting",
            "user_type": "unknown",
            "intent": "greeting",
        }

    # 1.1 Global check for goodbye / farewell / exit to close with gratitude in customer's language
    farewell_keywords = [
        "bye", "goodbye", "thank you", "thanks", "that's all", "that is all",
        "nothing else", "no more questions", "exit", "quit",
        "നന്ദി", "ബൈ", "ശരി ബൈ", "മതി", "ഒന്നുമില്ല", "പോകട്ടെ", "താങ്ക്സ്", "താങ്ക് യു"
    ]
    if text and any(k in text for k in farewell_keywords):
        lang = session.get("language", "en")
        session["state"] = "open"
        if lang == "ml":
            farewell_msg = ("ബ്രിഡ്ജിയോൺ സ്കിൽവേഴ്സിറ്റിയുമായി ബന്ധപ്പെട്ടതിന് വളരെ നന്ദി. "
                            "ഞങ്ങളോടൊപ്പം നിങ്ങളുടെ കരിയർ മികച്ച രീതിയിൽ വളർത്തിയെടുക്കാൻ സാധിക്കുമെന്ന് ഞങ്ങൾ പ്രതീക്ഷിക്കുന്നു. നല്ലൊരു ദിവസം ആശംസിക്കുന്നു!")
        else:
            farewell_msg = ("Thank you so much for contacting Bridgeon Skillversity. "
                            "It was a pleasure speaking with you, and we look forward to helping you build a highly successful career. Have a wonderful day!")
        return {
            "response_text": farewell_msg,
            "state": "open",
            "user_type": session.get("user_type", "unknown"),
            "intent": "farewell",
        }

    # Check if they want info sent to WhatsApp/SMS
    whatsapp_request_keywords = ["whatsapp", "sms", "message", "send brochure", "send link", "send details", "വാട്സാപ്പ്", "ലിങ്ക് അയക്കൂ"]
    wants_send = any(k in text for k in whatsapp_request_keywords)
    
    if wants_send:
        phone = session.get("caller_number") or session["lead_data"].get("phone")
        has_valid_phone = phone and len("".join(filter(str.isdigit, phone))) >= 5
        
        if has_valid_phone:
            from app.services.messaging import send_whatsapp
            whatsapp_msg = (
                f"Hi there,\n\n"
                f"Here are the Bridgeon Skillversity course brochure details as requested:\n"
                f"👉 https://bridgeon.in/brochure.pdf\n\n"
                f"Our admissions counselor will call you shortly."
            )
            brochure_pdf = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            
            import asyncio
            try:
                asyncio.create_task(send_whatsapp(phone, whatsapp_msg, media_url=brochure_pdf))
            except Exception:
                pass
            
            if session.get("language") == "ml":
                msg = "തീർച്ചയായും! കോഴ്‌സിന്റെ ബ്രോഷറും ലിങ്കും ഞാൻ നിങ്ങളുടെ വാട്സാപ്പിലേക്ക് അയച്ചിട്ടുണ്ട്. ദയവായി പരിശോധിക്കുക."
            else:
                msg = "Sure! I have just sent the course brochure and registration link to your WhatsApp. Please check it."
                
            return {
                "response_text": msg,
                "state": session["state"],
                "user_type": session.get("user_type", "unknown"),
                "intent": "send_materials",
            }
        else:
            session["state"] = "lead_capture_phone"
            if session.get("language") == "ml":
                msg = "തീർച്ചയായും! കോഴ്‌സ് വിവരങ്ങൾ വാട്സാപ്പിൽ അയക്കാനായി നിങ്ങളുടെ ഫോൺ നമ്പർ ഒന്ന് പറയാമോ?"
            else:
                msg = "Sure! I'd love to send the brochure and details via WhatsApp. What is your phone number?"
                
            return {
                "response_text": msg,
                "state": "lead_capture_phone",
                "user_type": session.get("user_type", "unknown"),
                "intent": "request_phone_for_materials",
            }

    # Check for adaptive intent switching during scripted capture states
    intent_switch = await _check_intent_switch(raw_text, text, session, db)
    if intent_switch:
        interrupted_state = session["state"]
        session["interrupted_state"] = interrupted_state
        
        answer = intent_switch["answer"]
        intent = intent_switch["intent"]
        
        prompts = {
            "lead_capture_name": {
                "en": "By the way, to continue scheduling your counselor callback, may I know your name?",
                "ml": "അതുപോട്ടെ, കൗൺസിലറെക്കൊണ്ട് വിളിപ്പിക്കാനായി നിങ്ങളുടെ പേര് ഒന്ന് പറയാമോ?"
            },
            "lead_capture_phone": {
                "en": "By the way, to schedule that admissions call, what is the best phone number to reach you?",
                "ml": "അതുപോട്ടെ, നിങ്ങളെ കോൺടാക്ട് ചെയ്യേണ്ട ഫോൺ നമ്പർ ഒന്ന് പറയാമോ?"
            },
            "lead_capture_course": {
                "en": "By the way, which course interest track are you looking to enroll in?",
                "ml": "അതുപോട്ടെ, നിങ്ങൾ ഏത് കോഴ്സ് പഠിക്കാനാണ് ആഗ്രഹിക്കുന്നത്?"
            },
            "consent_whatsapp": {
                "en": "By the way, shall I send the course brochure to your WhatsApp?",
                "ml": "അതുപോട്ടെ, ഞാൻ കോഴ്സിന്റെ ബ്രോഷർ നിങ്ങളുടെ വാട്സാപ്പിലേക്ക് അയച്ചു തരട്ടെയോ?"
            }
        }
        
        lang = session.get("language", "en")
        guide_prompt = prompts[interrupted_state][lang]
        
        return {
            "response_text": f"{answer} {guide_prompt}",
            "state": interrupted_state,
            "user_type": session.get("user_type", "unknown"),
            "intent": intent,
        }

    # ── STATE: AFTER HOURS ───────────────────────────────────────────────────────
    if state == "after_hours":
        session["state"] = "lead_capture_name"
        session["user_type"] = "prospective"
        lang = session.get("language", "en")
        if lang == "ml":
            ah_msg = ("ഓഫീസ് സമയത്തിനു പുറത്ത് വിളിച്ചതിന് നന്ദി. "
                      "ഞങ്ങളുടെ അഡ്മിഷൻ ടീം തിരിച്ചു വിളിക്കാൻ "
                      "നിങ്ങളുടെ പേര് ഒന്ന് പറയാമോ?")
        else:
            ah_msg = ("Thank you for calling outside office hours. "
                      "May I take your name so our admissions team can call you back?")
        return {
            "response_text": ah_msg,
            "state": "lead_capture_name",
            "user_type": "prospective",
            "intent": "after_hours",
        }

    # ── STATE: GREETING ──────────────────────────────────────────────────────────
    if state == "greeting":
        lang = session.get("language", "en")
        
        # Check if the user is asking a question immediately after greeting (dynamic transition)
        rag_answer = await retrieve_grounded_answer_async(
            raw_text, db, language=lang, chat_history=session.get("chat_history")
        )
        if rag_answer:
            student_terms = ["class", "batch", "schedule", "deadline", "project", "mentor"]
            if any(t in text for t in student_terms):
                session["state"] = "student_faq"
                session["user_type"] = "student"
            else:
                session["state"] = "explore_courses"
                session["user_type"] = "prospective"
            return {
                "response_text": rag_answer,
                "state": session["state"],
                "user_type": session["user_type"],
                "intent": "rag_response",
            }

        student_keywords = [
            "student",
            "study",
            "studying",
            "mentor",
            "batch",
            "class",
            "schedule",
            "submission",
            "project",
            "assignment",
            "grade",
            "assessment",
            "attendance",
            "vidhyarthi",
            "പഠിക്കുന്നു",
            "ക്ലാസ്",
            "ബാച്ച്",
        ]
        explorer_keywords = [
            "explore",
            "course",
            "courses",
            "fee",
            "fees",
            "admission",
            "admissions",
            "join",
            "enroll",
            "pricing",
            "cost",
            "placement",
            "placements",
            "career",
            "job",
            "salary",
            "new",
            "ഫീസ്",
            "ചേരാൻ",
            "അഡ്മിഷൻ",
            "കോഴ്സ്",
            "പഠിക്കാൻ",
            "വിവരങ്ങൾ",
            "ഹലോ",
            "നമസ്കാരം",
            "എന്തൊക്കെ",
        ]

        is_student = any(k in text for k in student_keywords)
        is_explorer = any(k in text for k in explorer_keywords)

        if is_student:
            session["user_type"] = "student"
            session["state"] = "student_faq"
            if lang == "ml":
                msg = ("ബ്രിഡ്ജിയോൺ ക്ലാസ് ഷെഡ്യൂൾ, പ്രോജക്ട് ഡെഡ്‌ലൈൻ, "
                       "അല്ലെങ്കിൽ മെന്ററെ ബന്ധപ്പെടുത്തുന്ന കാര്യം — ഇതിൽ ഏതെങ്കിലും "
                       "സഹായം ആണോ വേണ്ടത്?")
            else:
                msg = ("Welcome back! I can help you check weekly batch schedules, "
                       "project deadlines, or alert your mentor to call you. "
                       "What would you like to check today?")
            return {
                "response_text": msg,
                "state": "student_faq",
                "user_type": "student",
                "intent": "student_check_in",
            }
        elif is_explorer:
            session["user_type"] = "prospective"
            session["state"] = "explore_courses"
            if lang == "ml":
                msg = ("ബ്രിഡ്ജിയോൺ MERN Stack, Python Full Stack, Flutter, "
                       "Data Science, UI/UX Design എന്നീ പ്രോഗ്രാമുകൾ ഓഫർ ചെയ്യുന്നു. "
                       "ഏത് കോഴ്‌സിനെക്കുറിച്ച് അറിയണം?")
            else:
                msg = ("Great! Bridgeon offers practical, project-based bootcamps in "
                       "MERN Stack, Python Full Stack, Flutter Mobile, Data Science, and UI/UX Design. "
                       "Which program or technology would you like to explore?")
            return {
                "response_text": msg,
                "state": "explore_courses",
                "user_type": "prospective",
                "intent": "explore_courses",
            }
        else:
            session["unclear_attempts"] = session.get("unclear_attempts", 0) + 1
            settings_data = get_settings(db)
            if (
                settings_data.get("escalation_enabled")
                and session["unclear_attempts"] >= settings_data.get("auto_escalate_after_attempts", 3)
            ):
                session["state"] = "escalated"
                return {
                    "response_text": _escalation_message(session, db),
                    "state": "escalated",
                    "user_type": "unknown",
                    "intent": "escalated",
                }
            if lang == "ml":
                unclear_msg = ("ക്ഷമിക്കണം, ശരിക്ക് മനസ്സിലായില്ല. "
                               "നിങ്ങൾ ബ്രിഡ്ജിയോൺ വിദ്യാർഥിയാണോ, "
                               "അതോ പുതിയ കോഴ്‌സ് അന്വേഷിക്കുകയാണോ?")
            else:
                unclear_msg = ("I didn't catch that clearly. Are you a student of Bridgeon, "
                               "or are you looking to enroll in one of our courses?")
            return {
                "response_text": unclear_msg,
                "state": "greeting",
                "user_type": "unknown",
                "intent": "unclear_user_type",
            }

    # ── STATE: EXPLORE COURSES ──────────────────────────────────────────────────
    if state == "explore_courses":
        fee_keywords = ["fee", "fees", "cost", "price", "pricing", "pay", "charges", "ഫീസ്", "പൈസ", "ചെലവ്"]
        placement_keywords = [
            "placement",
            "placements",
            "job",
            "jobs",
            "salary",
            "package",
            "hire",
            "ജോലി",
            "ശമ്പളം",
            "പ്ലേസ്മെന്റ്"
        ]
        course_keywords = [
            "mern",
            "react",
            "python",
            "flutter",
            "data science",
            "data",
            "design",
            "ui",
            "ux",
            "java",
        ]

        lang = session.get("language", "en")
        if any(k in text for k in fee_keywords) or "callback" in text or "call" in text or "കോൾ" in text:
            trans = _transition_to_next_capture_state(session)
            if lang == "ml":
                fee_msg = ("ഓരോ കോഴ്‌സിന്റെയും ഫീ പ്ലാൻ അനുസരിച്ച് വ്യത്യസ്തമാണ്. "
                           f"ഞങ്ങളുടെ അഡ്മിഷൻ ടീം നിങ്ങൾക്ക് വിളിക്കും. {trans['response_text']}")
            else:
                fee_msg = ("Course fees vary by program and payment plans. "
                           "To give you accurate fee details, I will arrange a quick callback "
                           f"from our admissions team. {trans['response_text']}")
            return {
                "response_text": fee_msg,
                "state": trans["state"],
                "user_type": "prospective",
                "intent": "ask_fee_callback",
            }
        elif any(k in text for k in placement_keywords):
            if lang == "ml":
                pl_msg = ("ബ്രിഡ്ജിയോൺ 100% പ്ലേസ്മെന്റ് സഹായം നൽകുന്നു. "
                          "ഞങ്ങളുടെ ഡെവലപ്പർമാർ 2.5 LPA മുതൽ 4.9+ LPA വരെ ശമ്പളത്തിൽ "
                          "ജോലി ചെയ്യുന്നു. അഡ്മിഷൻ ടീം നിങ്ങൾക്ക് വിളിക്കട്ടെയോ?")
            else:
                pl_msg = ("Bridgeon provides 100% placement support, and our developers are placed "
                          "with starting salary ranges of 2.5 LPA to 4.9+ LPA depending on skillset. "
                          "Would you like me to organize a callback from admissions to discuss enrollment?")
            return {
                "response_text": pl_msg,
                "state": "explore_courses",
                "user_type": "prospective",
                "intent": "placement_queries",
            }
        elif any(k in text for k in course_keywords):
            matched = "selected program"
            for c in course_keywords:
                if c in text:
                    matched = c.upper()
                    break
            if lang == "ml":
                course_msg = (f"ഞങ്ങളുടെ {matched} പ്രോഗ്രാം 8 മുതൽ 10 മാസം വരെ നീണ്ടുനിൽക്കുന്നു. "
                              "മുൻ അനുഭവം ആവശ്യമില്ല. അഡ്മിഷൻ ഫീ വിശദീകരിക്കാൻ കോൾ ഷെഡ്യൂൾ ചെയ്യട്ടെയോ?")
            else:
                course_msg = (f"Our {matched} program runs for 8 to 10 months and is structured as a practical, "
                              "industry-simulator course. No prior coding experience is required to start. "
                              "Shall I schedule a call back to explain admissions and fees?")
            return {
                "response_text": course_msg,
                "state": "explore_courses",
                "user_type": "prospective",
                "intent": "course_info",
            }

        # Check local/enhanced RAG next
        rag_answer = await retrieve_grounded_answer_async(raw_text, db, language=session.get("language", "en"), chat_history=session.get("chat_history"))
        if rag_answer:
            return {
                "response_text": rag_answer,
                "state": "explore_courses",
                "user_type": "prospective",
                "intent": "rag_response",
            }

        # Otherwise fallback to callback transition
        record_knowledge_gap(db, raw_text, category="Course Info")
        trans = _transition_to_next_capture_state(session)
        if lang == "ml":
            callback_msg = f"കൂടുതൽ സഹായത്തിനായി ഞാൻ നിങ്ങളെ ശരിയായ വിഭാഗവുമായി ബന്ധിപ്പിക്കാം. {trans['response_text']}"
        else:
            callback_msg = f"I’ll connect you to the right department for further assistance. {trans['response_text']}"
        return {
            "response_text": callback_msg,
            "state": trans["state"],
            "user_type": "prospective",
            "intent": "request_callback",
        }

    # ── STATE: LEAD CAPTURE (NAME) ──────────────────────────────────────────────
    if state == "lead_capture_name":
        session["lead_data"]["name"] = raw_text
        session["state"] = "lead_capture_phone"
        lang = session.get("language", "en")
        if lang == "ml":
            name_msg = (f"{raw_text}, നിങ്ങളെ പരിചയപ്പെട്ടതിൽ സന്തോഷം! "
                        "ഞങ്ങളുടെ അഡ്മിഷൻ ടീം ബന്ധപ്പെടാൻ ഏറ്റവും നല്ല ഫോൺ നമ്പർ ഏതാണ്?")
        else:
            name_msg = (f"Nice to meet you, {raw_text}! "
                        "What is the best phone number for our admissions team to contact you?")
        return {
            "response_text": name_msg,
            "state": "lead_capture_phone",
            "user_type": "prospective",
            "intent": "capture_name",
        }

    # ── STATE: LEAD CAPTURE (PHONE) ─────────────────────────────────────────────
    if state == "lead_capture_phone":
        clean_num = "".join(filter(str.isdigit, text))
        lang = session.get("language", "en")
        if len(clean_num) >= 5:
            session["lead_data"]["phone"] = raw_text
            session["state"] = "lead_capture_course"
            if lang == "ml":
                phone_msg = ("ശരി! ഒടുവിലായി, ഏത് കോഴ്‌സ് ആണ് "
                             "നിങ്ങൾക്ക് ഏറ്റവും കൂടുതൽ താൽപ്പര്യം? "
                             "(MERN Stack, Python, Flutter, Data Science, UI/UX...)")
            else:
                phone_msg = ("Got it! And finally, which course or training track are you "
                             "most interested in? (MERN Stack, Python, Flutter, Data Science, UI/UX, etc.)")
            return {
                "response_text": phone_msg,
                "state": "lead_capture_course",
                "user_type": "prospective",
                "intent": "capture_phone",
            }
        else:
            if lang == "ml":
                invalid_msg = "ദയവായി ഒരു ശരിയായ ഫോൺ നമ്പർ നൽകൂ, ഞങ്ങളുടെ ടീം ബന്ധപ്പെടും."
            else:
                invalid_msg = "Please provide a valid phone number so our team can reach you."
            return {
                "response_text": invalid_msg,
                "state": "lead_capture_phone",
                "user_type": "prospective",
                "intent": "invalid_phone",
            }

    # ── STATE: LEAD CAPTURE (COURSE) ────────────────────────────────────────────
    if state == "lead_capture_course":
        session["lead_data"]["course"] = raw_text
        session["state"] = "consent_whatsapp"
        lang = session.get("language", "en")
        if lang == "ml":
            course_saved_msg = ("നല്ലത്! നിങ്ങളുടെ വിവരങ്ങൾ സേവ് ചെയ്തു. "
                                "ഒരു ബ്രിഡ്ജിയോൺ കൗൺസലർ ഒരു ബിസിനസ് ദിവസത്തിനകം "
                                "ബന്ധപ്പെടും. കോഴ്‌സ് ബ്രോഷർ WhatsApp-ൽ അയക്കട്ടെയോ?")
        else:
            course_saved_msg = ("Excellent! I have saved your details. A Bridgeon counselor "
                                "will contact you within one business day. "
                                "Shall I also send the course brochure to your WhatsApp number?")
        return {
            "response_text": course_saved_msg,
            "state": "consent_whatsapp",
            "user_type": "prospective",
            "intent": "capture_course",
        }

    # ── STATE: CONSENT WHATSAPP ─────────────────────────────────────────────────
    if state == "consent_whatsapp":
        yes_keywords = ["yes", "sure", "ok", "okay", "yeah", "send", "yup", "aam", "athe",
                        "ശരി", "അതെ", "ആം", "അയക്കൂ", "വേണം"]
        is_yes = any(k in text for k in yes_keywords)

        name = session["lead_data"]["name"] or "there"
        lang = session.get("language", "en")
        # Keep call alive — go to open free-form state instead of ending
        session["state"] = "open"

        if not session.get("lead_saved"):
            lead = leads.create_lead_record(
                db=db,
                name=session["lead_data"]["name"] or name,
                phone=session["lead_data"]["phone"] or "",
                course=session["lead_data"]["course"] or "Unknown",
                consent_whatsapp=is_yes,
                language=session.get("language", "en"),
                source="bot",
            )
            session["lead_data"]["lead_id"] = lead.id
            session["lead_saved"] = True

        if is_yes:
            session["consent_whatsapp"] = True
            if lang == "ml":
                consent_msg = (f"നല്ലത്, {name}! ബ്രോഷർ WhatsApp-ൽ അയച്ചു. "
                               "ഒരു ബ്രിഡ്ജിയോൺ കൗൺസലർ ഉടൻ ബന്ധപ്പെടും. "
                               "ഇനി ഞാൻ എന്തെങ്കിലും സഹായിക്കാൻ കഴിയുമോ? "
                               "കോഴ്‌സ് വിശദാംശങ്ങൾ, ഫീ, അല്ലെങ്കിൽ മറ്റ് ചോദ്യങ്ങൾ?")
            else:
                consent_msg = (f"Perfect, {name}! I have dispatched the brochure to your WhatsApp. "
                               "A Bridgeon counselor will reach out shortly. "
                               "Is there anything else I can help you with? "
                               "Feel free to ask about our courses, fees, placements, or anything else!")
            return {
                "response_text": consent_msg,
                "state": "open",
                "user_type": "prospective",
                "intent": "consent_granted",
                "lead_id": session["lead_data"].get("lead_id"),
            }
        else:
            session["consent_whatsapp"] = False
            if lang == "ml":
                no_consent_msg = (f"ശരി, {name}. ഞങ്ങൾ ഫോൺ കോൾ വഴി മാത്രം ബന്ധപ്പെടും. "
                                  "ഇനി ഞാൻ എന്തെങ്കിലും സഹായിക്കാൻ കഴിയുമോ? "
                                  "കോഴ്‌സ് വിശദാംശങ്ങൾ, ഫീ, പ്ലേസ്മെന്റ് — ചോദിക്കാം.")
            else:
                no_consent_msg = (f"No problem, {name}. We will follow up via phone call. "
                                  "Is there anything else I can help you with right now? "
                                  "Feel free to ask about our courses, fees, placements, or schedules!")
            return {
                "response_text": no_consent_msg,
                "state": "open",
                "user_type": "prospective",
                "intent": "consent_denied",
                "lead_id": session["lead_data"].get("lead_id"),
            }

    # ── STATE: STUDENT FAQ ──────────────────────────────────────────────────────
    if state == "student_faq":
        rag_answer = await retrieve_grounded_answer_async(raw_text, db, language=session.get("language", "en"), chat_history=session.get("chat_history"))
        if rag_answer:
            return {
                "response_text": rag_answer,
                "state": "student_faq",
                "user_type": "student",
                "intent": "rag_response",
            }

        schedule_keywords = ["schedule", "timing", "timings", "time", "date", "when is class",
                             "ഷെഡ്യൂൾ", "സമയം", "ക്ലാസ് എപ്പോൾ"]
        project_keywords = ["project", "submission", "deadline", "task", "upload", "submit",
                            "പ്രോജക്ട്", "ഡെഡ്‌ലൈൻ", "സബ്മിഷൻ"]
        mentor_keywords = ["mentor", "contact", "phone", "number", "speak to", "help",
                           "മെന്റർ", "ബന്ധപ്പെടണം", "ഫോൺ"]
        bye_keywords = ["bye", "quit", "exit", "thank", "നന്ദി", "ബൈ", "ശരി ബൈ", "പോകട്ടെ"]

        lang = session.get("language", "en")

        if any(k in text for k in schedule_keywords):
            if lang == "ml":
                sched_msg = ("നിങ്ങളുടെ ക്ലാസുകൾ തിങ്കൾ മുതൽ വെള്ളി വരെ രാവിലെ 10 മണി മുതൽ ഉച്ചയ്ക്ക് 1 മണി വരെയാണ് ഷെഡ്യൂൾ ചെയ്തിരിക്കുന്നത്. "
                             "ക്ലാസുകളിൽ കൃത്യത പാലിക്കുന്നത് വളരെ പ്രധാനമാണ്. പഠനത്തിൽ മികച്ച വിജയം ആശംസിക്കുന്നു!")
            else:
                sched_msg = ("Your classes are scheduled Monday to Friday from 10 AM to 1 PM. "
                             "Maintaining consistency is highly important for your growth. Keep up the wonderful work!")
            return {
                "response_text": sched_msg,
                "state": "student_faq",
                "user_type": "student",
                "intent": "check_schedule",
            }
        elif any(k in text for k in project_keywords):
            if lang == "ml":
                proj_msg = ("നിങ്ങളുടെ പ്രോജക്റ്റുകൾ സബ്മിറ്റ് ചെയ്യേണ്ട അവസാന സമയം വെള്ളിയാഴ്ച വൈകിട്ട് 5 മണിയാണ്. "
                             "കോഡിംഗ് ചെയ്യുമ്പോൾ ബുദ്ധിമുട്ടുകൾ ഉണ്ടാകുന്നത് സ്വാഭാവികമാണ്, എങ്കിലും ഇത് നിങ്ങളെ ഒരു പ്രൊഫഷണൽ ഡെവലപ്പർ ആകാൻ സഹായിക്കും. ഓരോ ഘട്ടമായി ചെയ്യൂ, നിങ്ങൾക്ക് തീർച്ചയായും ഇത് സാധിക്കും!")
            else:
                proj_msg = ("Your project submission deadline is Friday by 5 PM. "
                             "Working on industry projects can be challenging at times, but it is excellent preparation for your career. Take it step by step, you can absolutely do it!")
            return {
                "response_text": proj_msg,
                "state": "student_faq",
                "user_type": "student",
                "intent": "check_deadline",
            }
        elif any(k in text for k in mentor_keywords):
            if lang == "ml":
                mentor_msg = ("നിങ്ങളെ നേരിട്ട് ബന്ധപ്പെടാൻ ഞാൻ നിങ്ങളുടെ മെന്ററോട് ആവശ്യപ്പെടാം. "
                              "കൂടാതെ, നിങ്ങളുടെ സ്റ്റുഡന്റ് പോർട്ടൽ ഡാഷ്‌ബോർഡിലും മെന്ററുടെ കോൺടാക്ട് വിവരങ്ങൾ കാണാൻ സാധിക്കുന്നതാണ്.")
            else:
                mentor_msg = ("I will gladly notify your mentor to connect with you directly. "
                              "You can also easily find their contact information on your student portal dashboard.")
            return {
                "response_text": mentor_msg,
                "state": "student_faq",
                "user_type": "student",
                "intent": "contact_mentor",
            }
        elif any(k in text for k in bye_keywords):
            # Keep call alive — go to open state, don't end the call
            session["state"] = "open"
            if lang == "ml":
                bye_msg = ("ബ്രിഡ്ജിയോൺ സ്കിൽവേഴ്സിറ്റിയുമായി ബന്ധപ്പെട്ടതിന് വളരെ നന്ദി. "
                           "ഞങ്ങളോടൊപ്പം നിങ്ങളുടെ കരിയർ മികച്ച രീതിയിൽ വളർത്തിയെടുക്കാൻ സാധിക്കുമെന്ന് ഞങ്ങൾ പ്രതീക്ഷിക്കുന്നു. നല്ലൊരു ദിവസം ആശംസിക്കുന്നു!")
            else:
                bye_msg = ("Thank you so much for contacting Bridgeon Skillversity. "
                           "It was a pleasure speaking with you, and we look forward to helping you build a highly successful career. Have a wonderful day!")
            return {
                "response_text": bye_msg,
                "state": "open",
                "user_type": "student",
                "intent": "farewell",
            }
        else:
            record_knowledge_gap(db, raw_text, category="Student Support")
            if lang == "ml":
                support_msg = ("പ്രോഗ്രാമിംഗ് പഠിക്കുമ്പോൾ സംശയങ്ങൾ ഉണ്ടാകുന്നത് തികച്ചും സ്വാഭാവികമാണ്. "
                               "നിങ്ങളുടെ ചോദ്യം ഞാൻ മെന്റർക്ക് കൈമാറിയിട്ടുണ്ട്, അവർ ഉടൻ തന്നെ നിങ്ങളെ ബന്ധപ്പെടുന്നതായിരിക്കും. ഇതിനിടയിൽ, ക്ലാസ് ഷെഡ്യൂൾ അല്ലെങ്കിൽ പ്രോജക്റ്റ് ഡെഡ്‌ലൈൻ എന്നിവ പരിശോധിക്കാൻ ഞാൻ സഹായിക്കണോ?")
            else:
                support_msg = ("It is completely natural to face challenges in programming. "
                               "I have logged your question for your mentor, and they will reach out to you shortly. In the meantime, would you like me to help check your class schedule or project deadline?")
            return {
                "response_text": support_msg,
                "state": "student_faq",
                "user_type": "student",
                "intent": "motivational_support",
            }

    # ── STATE: ESCALATED ────────────────────────────────────────────────────────
    if state == "escalated":
        session["state"] = "open"
        lang = session.get("language", "en")
        if lang == "ml":
            esc_msg = ("ഒരു കൗൺസലർ ഉടൻ നിങ്ങളെ ബന്ധപ്പെടും. "
                       "ഇതിനിടെ, ഞാൻ കോഴ്‌സ്, ഫീ, പ്ലേസ്മെന്റ് "
                       "അല്ലെങ്കിൽ മറ്റ് ചോദ്യങ്ങൾക്ക് ഉത്തരം നൽകാം. ചോദിക്കൂ!")
        else:
            esc_msg = (_escalation_message(session, db) +
                       " In the meantime, I can still answer questions about our courses, "
                       "fees, placements, and more. What would you like to know?")
        return {
            "response_text": esc_msg,
            "state": "open",
            "user_type": session.get("user_type", "unknown"),
            "intent": "escalated",
        }

    # ── STATE: OPEN — free-form intelligent Q&A (call stays alive) ───────────────
    if state == "open":
        lang = session.get("language", "en")

        # Check for explicit goodbye / farewell — acknowledge but KEEP call alive
        farewell_keywords = ["bye", "goodbye", "thank you", "thanks", "that's all", "that is all",
                             "nothing else", "no more questions", "ബൈ", "നന്ദി", "ശരി ബൈ",
                             "മതി", "ഒന്നുമില്ല", "പോകട്ടെ"]
        is_farewell = any(k in text for k in farewell_keywords)
        if is_farewell:
            if lang == "ml":
                farewell_msg = ("ബ്രിഡ്ജിയോൺ സ്കിൽവേഴ്സിറ്റിയുമായി ബന്ധപ്പെട്ടതിന് വളരെ നന്ദി. "
                                "ഞങ്ങളോടൊപ്പം നിങ്ങളുടെ കരിയർ മികച്ച രീതിയിൽ വളർത്തിയെടുക്കാൻ സാധിക്കുമെന്ന് ഞങ്ങൾ പ്രതീക്ഷിക്കുന്നു. നല്ലൊരു ദിവസം ആശംസിക്കുന്നു!")
            else:
                farewell_msg = ("Thank you so much for contacting Bridgeon Skillversity. "
                                "It was a pleasure speaking with you, and we look forward to helping you build a highly successful career. Have a wonderful day!")
            return {
                "response_text": farewell_msg,
                "state": "open",
                "user_type": session.get("user_type", "unknown"),
                "intent": "farewell",
            }

        # Try RAG / knowledge base first
        rag_answer = await retrieve_grounded_answer_async(raw_text, db, language=lang, chat_history=session.get("chat_history"))
        if rag_answer:
            return {
                "response_text": rag_answer,
                "state": "open",
                "user_type": session.get("user_type", "unknown"),
                "intent": "rag_response",
            }

        # Fee / callback fallback
        fee_keywords = ["fee", "fees", "cost", "price", "pricing", "pay", "charges",
                        "ഫീസ്", "പൈസ", "ചെലവ്"]
        placement_keywords = ["placement", "job", "salary", "package", "hire",
                               "ജോലി", "ശമ്പളം", "പ്ലേസ്മെന്റ്"]
        if any(k in text for k in fee_keywords):
            if lang == "ml":
                reply = ("ഓരോ കോഴ്‌സിന്റെയും ഫീ വ്യത്യസ്തമാണ്. "
                         "ഞങ്ങളുടെ അഡ്മിഷൻ ടീം കൃത്യമായ വിവരങ്ങൾ നൽകും. "
                         "MERN Stack, Python, Flutter, Data Science, UI/UX — "
                         "ഏത് കോഴ്‌സ് ആണ് ആഗ്രഹിക്കുന്നത്?")
            else:
                reply = ("Course fees vary by program and payment plan. "
                         "Bridgeon offers EMI options to make it affordable. "
                         "Which course interests you — MERN Stack, Python, Flutter, Data Science, or UI/UX? "
                         "I can get you more specific details.")
            return {
                "response_text": reply,
                "state": "open",
                "user_type": session.get("user_type", "unknown"),
                "intent": "faq_response",
            }

        if any(k in text for k in placement_keywords):
            if lang == "ml":
                reply = ("ബ്രിഡ്ജിയോൺ 100% പ്ലേസ്മെന്റ് സഹായം നൽകുന്നു. "
                         "ഡെവലപ്പർമാർ 2.5 LPA മുതൽ 4.9+ LPA വരെ ശമ്പളത്തിൽ ജോലി ചെയ്യുന്നു. "
                         "മറ്റ് ചോദ്യങ്ങൾ ഉണ്ടോ?")
            else:
                reply = ("Bridgeon provides 100% placement support with dedicated career guidance. "
                         "Our graduates are placed at 2.5 LPA to 4.9+ LPA starting packages. "
                         "Is there anything specific about placements you'd like to know?")
            return {
                "response_text": reply,
                "state": "open",
                "user_type": session.get("user_type", "unknown"),
                "intent": "faq_response",
            }

        # Generic knowledgeable fallback — stay on call
        record_knowledge_gap(db, raw_text, category="Open Q&A")
        if lang == "ml":
            fallback = ("കൂടുതൽ സഹായത്തിനായി ഞാൻ നിങ്ങളെ ശരിയായ വിഭാഗവുമായി ബന്ധിപ്പിക്കാം. "
                        "ഇതിനിടെ, AI, ഡാറ്റ സയൻസ്, അല്ലെങ്കിൽ ഫ്ലട്ടർ — ഇതിൽ ഏത് കോഴ്‌സിലാണ് താൽപ്പര്യം?")
        else:
            fallback = ("I’ll connect you to the right department for further assistance. "
                        "In the meantime, feel free to ask about our main programs like AI, Data Science, and Flutter. "
                        "Which course are you most interested in?")
        return {
            "response_text": fallback,
            "state": "open",
            "user_type": session.get("user_type", "unknown"),
            "intent": "faq_response",
        }

    # ── STATE: ENDED — redirect to open to keep call alive ───────────────────────
    if state == "ended":
        lang = session.get("language", "en")
        session["state"] = "open"
        if lang == "ml":
            continue_msg = ("ഇനിയും ഞാൻ സഹായിക്കാൻ ഇവിടെ ഉണ്ട്. "
                            "കോഴ്‌സ്, ഫീ, പ്ലേസ്മെന്റ് — "
                            "ഏത് ചോദ്യവും ചോദിക്കൂ!")
        else:
            continue_msg = ("I'm still here if you have more questions! "
                            "Feel free to ask about our courses, fees, placements, "
                            "or anything else about Bridgeon Skillversity.")
        return {
            "response_text": continue_msg,
            "state": "open",
            "user_type": session.get("user_type", "unknown"),
            "intent": "greeting",
        }

    return {
        "response_text": _greeting_text(session.get("language", "en"), db),
        "state": "greeting",
        "user_type": "unknown",
        "intent": "default",
    }


@router.post("/reset", summary="Clear and reset chat session state")
async def reset(payload: ResetPayload, db: Session = Depends(get_db)):
    """
    Clears session state to allow starting a new simulation call.
    """
    session_id = payload.session_id
    session_obj = db.query(BotSession).filter(BotSession.session_id == session_id).first()
    if session_obj:
        session_obj.session_data = _get_initial_session()
        flag_modified(session_obj, "session_data")
        session_obj.updated_at = datetime.now(timezone.utc)
        db.commit()
    else:
        initial_data = _get_initial_session()
        session_obj = BotSession(session_id=session_id, session_data=initial_data)
        db.add(session_obj)
        db.commit()
    return {"status": "success", "message": f"Session {session_id} reset successfully"}