import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from app.core.models import Lead
from app.services import messaging


@pytest.fixture
def dummy_lead():
    return Lead(
        id=42,
        name="Test Student",
        phone="+919999999999",
        course="MERN Stack",
        consent_whatsapp=True,
        language="en",
        source="bot"
    )


# ─── Tests for Simulation Fallback Mode ───────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.messaging.logger")
@patch("app.core.config.settings.TWILIO_ACCOUNT_SID", "")
async def test_send_whatsapp_simulation(mock_logger):
    # Ensure it returns True and logs the simulation message
    res = await messaging.send_whatsapp("+919999999999", "Hello WhatsApp")
    assert res is True
    mock_logger.info.assert_called_once_with(
        "[SIMULATION - WHATSAPP] To: +919999999999 | Message: Hello WhatsApp"
    )


@pytest.mark.asyncio
@patch("app.services.messaging.logger")
@patch("app.core.config.settings.TWILIO_ACCOUNT_SID", "")
async def test_send_sms_simulation(mock_logger):
    # Ensure it returns True and logs the simulation message
    res = await messaging.send_sms("+919999999999", "Hello SMS")
    assert res is True
    mock_logger.info.assert_called_once_with(
        "[SIMULATION - SMS] To: +919999999999 | Message: Hello SMS"
    )


@pytest.mark.asyncio
@patch("app.services.messaging.logger")
@patch("app.core.config.settings.SMTP_USER", "")
async def test_send_email_simulation(mock_logger):
    # Ensure it returns True and logs the simulation message
    res = await messaging.send_email("admin@test.com", "Test Subject", "<h1>Test Body</h1>")
    assert res is True
    assert mock_logger.info.call_args[0][0].startswith("[SIMULATION - EMAIL] To: admin@test.com | Subject: Test Subject")


# ─── Tests for Live Integration Mode ──────────────────────────────────────────

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_whatsapp_live_success(mock_post):
    # Mock successful response
    mock_post.return_value = MagicMock(status_code=201, is_success=True)

    with patch("app.core.config.settings.TWILIO_ACCOUNT_SID", "ACxxxxxx"), \
         patch("app.core.config.settings.TWILIO_AUTH_TOKEN", "fake_token"):
        res = await messaging.send_whatsapp("+919999999999", "Hello WhatsApp", media_url="http://test.pdf")
        
        assert res is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["data"]["To"] == "whatsapp:+919999999999"
        assert kwargs["data"]["Body"] == "Hello WhatsApp"
        assert kwargs["data"]["MediaUrl"] == "http://test.pdf"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_send_sms_live_success(mock_post):
    # Mock successful response
    mock_post.return_value = MagicMock(status_code=201, is_success=True)

    with patch("app.core.config.settings.TWILIO_ACCOUNT_SID", "ACxxxxxx"), \
         patch("app.core.config.settings.TWILIO_AUTH_TOKEN", "fake_token"):
        res = await messaging.send_sms("+919999999999", "Hello SMS")
        
        assert res is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["data"]["To"] == "+919999999999"
        assert kwargs["data"]["Body"] == "Hello SMS"


@pytest.mark.asyncio
@patch("smtplib.SMTP")
async def test_send_email_live_success(mock_smtp_class):
    mock_smtp = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp

    with patch("app.core.config.settings.SMTP_HOST", "smtp.test.com"), \
         patch("app.core.config.settings.SMTP_USER", "user@test.com"), \
         patch("app.core.config.settings.SMTP_PASSWORD", "pass"):
        res = await messaging.send_email("recipient@test.com", "Subject", "Body")
        
        assert res is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user@test.com", "pass")
        mock_smtp.sendmail.assert_called_once()


# ─── Tests for Routing Logic (PRD 9.5) ────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.messaging.send_whatsapp", new_callable=AsyncMock)
@patch("app.services.messaging.send_sms", new_callable=AsyncMock)
@patch("app.services.messaging.send_email", new_callable=AsyncMock)
async def test_dispatch_lead_notifications_consent_whatsapp(mock_email, mock_sms, mock_whatsapp, dummy_lead):
    # Consent is True -> WhatsApp brochure sent, no SMS
    dummy_lead.consent_whatsapp = True
    db_mock = MagicMock()

    await messaging.dispatch_lead_notifications(dummy_lead, db_mock)

    mock_whatsapp.assert_called_once()
    mock_sms.assert_not_called()
    mock_email.assert_called_once()
    
    # Check that brochure link is sent
    whatsapp_args = mock_whatsapp.call_args[0]
    assert dummy_lead.phone in whatsapp_args[0]
    assert "https://bridgeon.in/brochure.pdf" in whatsapp_args[1]


@pytest.mark.asyncio
@patch("app.services.messaging.send_whatsapp", new_callable=AsyncMock)
@patch("app.services.messaging.send_sms", new_callable=AsyncMock)
@patch("app.services.messaging.send_email", new_callable=AsyncMock)
async def test_dispatch_lead_notifications_no_consent(mock_email, mock_sms, mock_whatsapp, dummy_lead):
    # Consent is False -> SMS sent, no WhatsApp
    dummy_lead.consent_whatsapp = False
    db_mock = MagicMock()

    await messaging.dispatch_lead_notifications(dummy_lead, db_mock)

    mock_whatsapp.assert_not_called()
    mock_sms.assert_called_once()
    mock_email.assert_called_once()

    # Check SMS content
    sms_args = mock_sms.call_args[0]
    assert dummy_lead.phone in sms_args[0]
    assert "admissions team" in sms_args[1]
