"""
Basic API tests for production readiness (Phase 12).
"""
import os
# Force empty API keys for unit testing to prevent live API calls and timeouts
os.environ["OPENAI_API_KEY"] = ""
os.environ["SARVAM_API_KEY"] = ""
os.environ["ELEVENLABS_API_KEY"] = ""
os.environ["EXOTEL_API_KEY"] = ""
os.environ["EXOTEL_API_TOKEN"] = ""
os.environ["EXOTEL_ACCOUNT_SID"] = ""
os.environ["GEMMA_API_KEY"] = ""
os.environ["GEMMA_API_BASE"] = ""

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.auth import issue_admin_token
from main import app

client = TestClient(app)

# Mock vector store queries to prevent loading HuggingFace embedding models
from unittest.mock import MagicMock
import app.core.vectorstore
app.core.vectorstore.query_documents = MagicMock(return_value=[])



def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data


def test_readiness_endpoint():
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_bot_greeting_uses_settings():
    response = client.post(
        "/api/v1/bot/chat",
        json={"text": "__START__", "session_id": "test-session-settings"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response_text" in data
    assert "engine_mode" in data
    assert data["intent"] == "greeting"


def test_dashboard_requires_auth():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


def test_dashboard_stats_with_auth():
    token = issue_admin_token("admin")
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "stats" in response.json()


def test_telephony_inbound_call():
    response = client.post(
        "/api/v1/telephony/inbound",
        json={
            "caller": "+91 9876543210",
            "text": "I want to know about Python course fees",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["call_id"].startswith("call-")
    assert data["bot_response"]


@patch("app.core.config.settings.OPENAI_API_KEY", "")
@patch("app.core.config.settings.GEMMA_API_KEY", "")
@patch("app.core.config.settings.GEMMA_API_BASE", "")
def test_voice_status_endpoint():
    response = client.get("/api/v1/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert "stt" in data
    assert "tts" in data
    assert data["openai_configured"] is False
    assert data["gemma_configured"] is False

def test_voice_training_requires_auth():
    response = client.post(
        "/api/v1/training/voice",
        json={
            "audio_question_base64": "dGVzdF9xdWVzdGlvbg==",
            "audio_answer_base64": "dGVzdF9hbnN3ZXI=",
            "language": "en",
            "category": "General",
        },
    )
    assert response.status_code == 401


@patch("app.services.voice.transcribe_audio")
def test_voice_training_authorized_fail_no_provider(mock_transcribe):
    mock_transcribe.return_value = ""
    token = issue_admin_token("admin")
    response = client.post(
        "/api/v1/training/voice",
        json={
            "audio_question_base64": "dGVzdF9xdWVzdGlvbg==",
            "audio_answer_base64": "dGVzdF9hbnN3ZXI=",
            "language": "en",
            "category": "General",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert "Server STT transcription yielded empty text" in response.json()["detail"]


@patch("app.services.voice.transcribe_audio")
def test_voice_training_success_with_mock_stt(mock_transcribe):
    mock_transcribe.side_effect = ["Mock Question", "Mock Answer"]

    token = issue_admin_token("admin")
    response = client.post(
        "/api/v1/training/voice",
        json={
            "audio_question_base64": "dGVzdF9xdWVzdGlvbg==",
            "audio_answer_base64": "dGVzdF9hbnN3ZXI=",
            "language": "en",
            "category": "General",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["entry"]["question_en"] == "Mock Question"
    assert data["entry"]["answer_en"] == "Mock Answer"


def test_twilio_inbound_webhook():
    response = client.post(
        "/api/v1/telephony/twilio/inbound/webhook",
        data={"From": "+12345"}
    )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text


@patch("app.api.v1.endpoints.telephony.transcribe_audio")
def test_twilio_inbound_recording(mock_transcribe):
    mock_transcribe.return_value = "Tell me about course fees"
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.content = b"fake audio"
        mock_get.return_value.status_code = 200
        mock_get.return_value.is_success = True
        
        with patch("app.core.config.settings.TWILIO_ACCOUNT_SID", "ACxxxxxx"), \
             patch("app.core.config.settings.TWILIO_AUTH_TOKEN", "fake_token"):
            response = client.post(
                "/api/v1/telephony/twilio/inbound/recording?session_id=tw-test&caller=%2B12345&language=en",
                data={"RecordingUrl": "http://example.com/recording.wav"}
            )
            assert response.status_code == 200
            assert "application/xml" in response.headers["content-type"]
            assert "<Response>" in response.text


def test_twilio_outbound_webhook():
    response = client.post(
        "/api/v1/telephony/twilio/outbound/webhook?session_id=tw-test&language=en&message=TestCampaign",
    )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text
    assert "TestCampaign" in response.text


def test_twilio_outbound_status():
    response = client.post(
        "/api/v1/telephony/twilio/outbound/status",
        data={"CallStatus": "completed", "CallDuration": "45"}
    )
    assert response.status_code == 200
    assert response.json() == {"received": True, "status": "completed", "duration": "45"}


def test_bot_session_persistence():
    session_id = "test-persistent-session-unique-123"
    
    # 1. Reset first to clean up if it exists
    reset_resp = client.post("/api/v1/bot/reset", json={"session_id": session_id})
    assert reset_resp.status_code == 200
    
    # 2. Query database directly to verify initial session state
    from app.core.database import SessionLocal
    from app.core.models import BotSession
    
    db = SessionLocal()
    try:
        session_obj = db.query(BotSession).filter(BotSession.session_id == session_id).first()
        assert session_obj is not None
        assert session_obj.session_data["state"] == "greeting"
        
        # 3. Perform a chat turn to change the session state
        chat_resp = client.post(
            "/api/v1/bot/chat",
            json={"text": "I want to explore courses", "session_id": session_id}
        )
        assert chat_resp.status_code == 200
        
        # 4. Query database to verify state has changed in the database
        db.refresh(session_obj)
        assert session_obj.session_data["state"] == "explore_courses"
        
        # 5. Reset again
        client.post("/api/v1/bot/reset", json={"session_id": session_id})
        db.refresh(session_obj)
        assert session_obj.session_data["state"] == "greeting"
    finally:
        db.close()


def test_bot_emotion_detection():
    # Test frustrated emotion prepending
    session_id = "test-emotion-frustrated"
    client.post("/api/v1/bot/reset", json={"session_id": session_id})
    
    # First turn
    client.post("/api/v1/bot/chat", json={"text": "__START__", "session_id": session_id})
    
    # Frustrated input
    response = client.post(
        "/api/v1/bot/chat",
        json={"text": "This is stupid and useless, show me courses", "session_id": session_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["emotion"] == "frustrated"
    assert "frustrated" in data["response_text"] or "I understand this is frustrating" in data["response_text"]


def test_bot_long_term_memory_greeting():
    from app.core.database import SessionLocal
    from app.core.models import Lead, BotSession
    
    db = SessionLocal()
    phone = "9999988888"
    try:
        # Clean up existing lead if any
        db.query(Lead).filter(Lead.phone == phone).delete()
        session_id = "test-ltm-session"
        db.query(BotSession).filter(BotSession.session_id == session_id).delete()
        db.commit()
        
        # Add new lead
        lead = Lead(name="Arun Test", phone=phone, course="MERN Stack", consent_whatsapp=True, language="en", source="bot")
        db.add(lead)
        db.commit()
        
        # Start chat session passing caller_number
        response = client.post(
            "/api/v1/bot/chat",
            json={"text": "__START__", "session_id": session_id, "caller_number": phone}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "Arun Test" in data["response_text"]
        assert "MERN" in data["response_text"]
    finally:
        db.query(Lead).filter(Lead.phone == phone).delete()
        db.commit()
        db.close()


@patch("app.services.voice.search_company_info")
def test_bot_adaptive_intent_switching(mock_search):
    mock_search.return_value = "No results found."
    session_id = "test-adaptive-switch"
    client.post("/api/v1/bot/reset", json={"session_id": session_id})
    
    # 1. Start the call
    client.post("/api/v1/bot/chat", json={"text": "__START__", "session_id": session_id})
    
    # 2. Pivot to exploring courses
    client.post("/api/v1/bot/chat", json={"text": "I want to explore courses", "session_id": session_id})
    
    # 3. Trigger lead capture flow via fallback (knowledge gap)
    resp = client.post("/api/v1/bot/chat", json={"text": "xyz123abc", "session_id": session_id})
    assert resp.status_code == 200
    assert "May I know your name first, please?" in resp.json()["response_text"]
    
    # Current state should be lead_capture_name
    # 4. Instead of giving a name, ask an unexpected question about placements
    resp_switch = client.post("/api/v1/bot/chat", json={"text": "Wait, do you have placements?", "session_id": session_id})
    assert resp_switch.status_code == 200
    data = resp_switch.json()
    
    # The bot should answer the placement question AND prompt back for their name
    assert "placement" in data["response_text"].lower() or "salary" in data["response_text"].lower()
    assert "may I know your name" in data["response_text"]
    assert data["state"] == "lead_capture_name"


def test_upload_url_requires_auth():
    response = client.post("/api/v1/knowledge/upload-url", json={"url": "https://bridgeon.in"})
    assert response.status_code == 401


@patch("app.services.url_ingest.ingest_url")
def test_upload_url_authorized_success(mock_ingest_url):
    mock_ingest_url.return_value = None
    token = issue_admin_token("admin")
    response = client.post(
        "/api/v1/knowledge/upload-url",
        json={"url": "https://bridgeon.in/about"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "Successfully ingested" in response.json()["message"]


@patch("duckduckgo_search.DDGS.text")
def test_search_company_info_general(mock_ddgs_text):
    mock_ddgs_text.return_value = [
        {"title": "What is React?", "body": "React is a JavaScript library for building user interfaces.", "href": "https://react.dev"}
    ]
    from app.services.voice import search_company_info
    res = search_company_info("React library")
    assert "What is React?" in res
    assert "React is a JavaScript library" in res
    assert "https://react.dev" in res




