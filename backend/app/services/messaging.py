import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.models import Lead

logger = logging.getLogger("uvicorn")


async def send_whatsapp(to_number: str, body: str, media_url: Optional[str] = None) -> bool:
    """
    Send a WhatsApp message using Twilio WhatsApp API, or fallback to simulation mode.
    """
    to_formatted = to_number.strip()
    if not to_formatted.startswith("+"):
        to_formatted = f"+{to_formatted}"

    if settings.twilio_configured:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            data = {
                "From": settings.TWILIO_WHATSAPP_NUMBER,
                "To": f"whatsapp:{to_formatted}",
                "Body": body,
            }
            if media_url:
                data["MediaUrl"] = media_url

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    data=data,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
                if resp.is_success:
                    logger.info(f"[WHATSAPP] Sent successfully to {to_formatted} via Twilio.")
                    return True
                else:
                    logger.error(f"[WHATSAPP] Twilio send failed ({resp.status_code}): {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"[WHATSAPP] Error connecting to Twilio: {str(e)}")
            return False
    else:
        # Simulation Mode
        media_str = f" | MediaUrl: {media_url}" if media_url else ""
        logger.info(f"[SIMULATION - WHATSAPP] To: {to_formatted} | Message: {body}{media_str}")
        return True


async def send_sms(to_number: str, body: str) -> bool:
    """
    Send an SMS using Twilio SMS API, or fallback to simulation mode.
    """
    to_formatted = to_number.strip()
    if not to_formatted.startswith("+"):
        to_formatted = f"+{to_formatted}"

    if settings.twilio_configured:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            data = {
                "From": settings.TWILIO_PHONE_NUMBER,
                "To": to_formatted,
                "Body": body,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    data=data,
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
                if resp.is_success:
                    logger.info(f"[SMS] Sent successfully to {to_formatted} via Twilio.")
                    return True
                else:
                    logger.error(f"[SMS] Twilio send failed ({resp.status_code}): {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"[SMS] Error connecting to Twilio: {str(e)}")
            return False
    else:
        # Simulation Mode
        logger.info(f"[SIMULATION - SMS] To: {to_formatted} | Message: {body}")
        return True


async def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email using SMTP or fallback to simulation mode.
    """
    if settings.smtp_configured:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            part = MIMEText(html_body, "html")
            msg.attach(part)

            # Connect and send in a blocking setup (run in threadpool if needed, but keeping it direct for simple stack)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            
            logger.info(f"[EMAIL] Sent successfully to {to_email} via SMTP.")
            return True
        except Exception as e:
            logger.error(f"[EMAIL] SMTP send failed: {str(e)}")
            return False
    else:
        # Simulation Mode
        logger.info(f"[SIMULATION - EMAIL] To: {to_email} | Subject: {subject} | Body: {html_body[:200]}...")
        return True


async def dispatch_lead_notifications(lead: Lead, db: Session) -> None:
    """
    Implements Channel Routing Logic (PRD 9.5) when a new lead is captured.
    - If WhatsApp consent is granted: Send rich course brochure via WhatsApp.
    - Else: Send SMS text confirmation.
    - Always: Dispatch email notification to admissions team with full lead data.
    """
    logger.info(f"[MESSAGING] Dispatching routing logic for Lead ID {lead.id} ({lead.name})")

    # 1. WhatsApp or SMS based on consent
    if lead.consent_whatsapp:
        # Send WhatsApp brochure link
        whatsapp_msg = (
            f"Hi {lead.name},\n\n"
            f"Thank you for contacting Bridgeon Skillversity! We are excited to share our "
            f"{lead.course} program details. Click the link below to view the syllabus and course brochure:\n"
            f"👉 https://bridgeon.in/brochure.pdf\n\n"
            f"Our admissions counselor will call you shortly."
        )
        # Sandbox PDF url for media testing
        brochure_pdf = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        await send_whatsapp(lead.phone, whatsapp_msg, media_url=brochure_pdf)
    else:
        # Send SMS text confirmation
        sms_msg = (
            f"Hi {lead.name}, thanks for your interest in Bridgeon. Our admissions team will "
            f"contact you shortly regarding the {lead.course} course. Helpline: 09513886363"
        )
        await send_sms(lead.phone, sms_msg)

    # 2. Email notification to admissions team
    email_subject = f"🚨 New Lead Captured: {lead.name} ({lead.course})"
    email_html = f"""
    <html>
        <body>
            <h2>New Prospective Student Inquiry</h2>
            <table border="1" cellpadding="8" style="border-collapse: collapse; font-family: sans-serif;">
                <tr bgcolor="#f2f2f2">
                    <th>Field</th>
                    <th>Details</th>
                </tr>
                <tr>
                    <td><strong>Name</strong></td>
                    <td>{lead.name}</td>
                </tr>
                <tr>
                    <td><strong>Phone</strong></td>
                    <td>{lead.phone}</td>
                </tr>
                <tr>
                    <td><strong>Course Interest</strong></td>
                    <td>{lead.course}</td>
                </tr>
                <tr>
                    <td><strong>WhatsApp Consent</strong></td>
                    <td>{"Yes (Brochure Sent)" if lead.consent_whatsapp else "No"}</td>
                </tr>
                <tr>
                    <td><strong>Preffered Language</strong></td>
                    <td>{lead.language}</td>
                </tr>
                <tr>
                    <td><strong>Source</strong></td>
                    <td>{lead.source}</td>
                </tr>
                <tr>
                    <td><strong>Timestamp (UTC)</strong></td>
                    <td>{lead.created_at.strftime('%Y-%m-%d %H:%M:%S') if lead.created_at else 'N/A'}</td>
                </tr>
            </table>
            <p style="margin-top: 15px;">Please assign a counselor to follow up with this lead within one business day.</p>
        </body>
    </html>
    """
    await send_email(settings.ADMISSIONS_EMAIL, email_subject, email_html)
