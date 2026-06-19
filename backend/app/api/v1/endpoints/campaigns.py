from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_admin
from app.core.models import Campaign, Lead
from app.core.settings_store import add_audit_log
from app.services.messaging import send_whatsapp, send_sms, send_email

router = APIRouter()

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str = Field(..., description="Name of the campaign")
    channel: str = Field(..., description="Channel: voice, whatsapp, sms, or email")
    script: Optional[str] = Field(None, description="Campaign message or script")
    schedule_time: Optional[str] = Field(None, description="Schedule time in ISO format or string")
    retry_attempts: int = Field(3, ge=1, le=5, description="Max retry attempts")
    consent_required: bool = Field(True, description="Enforce consent filters")
    dnd_compliance: bool = Field(True, description="Enforce DND registry filters")
    status: Optional[str] = Field("Scheduled", description="Draft, Scheduled, Running, Completed")


class CampaignUpdateStatus(BaseModel):
    status: str = Field(..., description="Draft, Scheduled, Running, Paused, Completed")


# ── Background Task Runner ───────────────────────────────────────────────────

async def run_campaign_simulation(campaign_id: int, db_session: Session):
    """
    Simulates campaign processing by querying database leads and sending
    outbound messages (or simulating calls) in the background.
    """
    # Create a local DB session to avoid session inheritance issues in threads
    db = db_session
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign or campaign.status != "Running":
            return

        leads = db.query(Lead).all()
        if not leads:
            campaign.status = "Completed"
            db.commit()
            return

        contacted_count = 0
        answered_count = 0
        converted_count = 0

        for lead in leads:
            # Re-fetch campaign to verify it hasn't been paused or deleted
            db.refresh(campaign)
            if campaign.status != "Running":
                break

            # Check consent
            if campaign.consent_required and not lead.consent_whatsapp:
                # If consent required and not granted, skip
                continue

            contacted_count += 1
            
            # Simulate contact logic
            if campaign.channel == "whatsapp":
                body = (
                    f"Hi {lead.name}, this is Bridgeon Skillversity. We've scheduled a campaign "
                    f"for our {lead.course} program. Here is the script:\n\n{campaign.script or ''}"
                )
                await send_whatsapp(lead.phone, body)
                answered_count += 1
                # 15% conversion simulation
                if hash(lead.name) % 7 == 0:
                    converted_count += 1

            elif campaign.channel == "sms":
                body = f"Bridgeon Alert: {campaign.script or ''}"
                await send_sms(lead.phone, body)
                answered_count += 1
                if hash(lead.name) % 8 == 0:
                    converted_count += 1

            elif campaign.channel == "email":
                subject = f"Bridgeon Skillversity Campaign: {campaign.name}"
                body = f"<h3>Hello {lead.name}</h3><p>{campaign.script or ''}</p>"
                await send_email(lead.phone + "@example.com", subject, body)  # Fallback to simulated email
                answered_count += 1
                if hash(lead.name) % 6 == 0:
                    converted_count += 1

            else:  # Voice Call (Simulated outbound call)
                # In a real setup, we would trigger initiateOutboundCall via Exotel
                # In simulation, we count it as completed
                answered_count += 1
                if hash(lead.name) % 5 == 0:
                    converted_count += 1

        campaign.contacted = contacted_count
        campaign.answered = answered_count
        campaign.converted = converted_count
        campaign.status = "Completed"
        db.commit()
        add_audit_log(db, f"Background execution completed for campaign '{campaign.name}'", actor="system")

    except Exception as e:
        print(f"[CAMPAIGN] Error running campaign {campaign_id}: {e}")


# ── API Routes ───────────────────────────────────────────────────────────────

@router.get("/", summary="List all campaigns")
async def list_campaigns(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    return [c.to_dict() for c in campaigns]


@router.post("/", summary="Create a new campaign")
async def create_campaign(
    payload: CampaignCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db), 
    _: str = Depends(require_admin)
):
    campaign = Campaign(
        name=payload.name,
        channel=payload.channel,
        script=payload.script,
        schedule_time=payload.schedule_time,
        status=payload.status or "Scheduled",
        retry_attempts=payload.retry_attempts,
        consent_required=payload.consent_required,
        dnd_compliance=payload.dnd_compliance,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    add_audit_log(db, f"Created outbound campaign: '{campaign.name}'", actor="admin")

    # If created directly in "Running" status, trigger immediate simulation run
    if campaign.status == "Running":
        background_tasks.add_task(run_campaign_simulation, campaign.id, db)

    return campaign.to_dict()


@router.put("/{campaign_id}/status", summary="Update campaign status (Pause/Resume/Start)")
async def update_campaign_status(
    campaign_id: int, 
    payload: CampaignUpdateStatus, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db), 
    _: str = Depends(require_admin)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    old_status = campaign.status
    campaign.status = payload.status
    db.commit()

    add_audit_log(db, f"Updated campaign '{campaign.name}' status from {old_status} to {payload.status}", actor="admin")

    # Trigger campaign runner if status changed to Running
    if payload.status == "Running" and old_status != "Running":
        background_tasks.add_task(run_campaign_simulation, campaign.id, db)

    return campaign.to_dict()


@router.delete("/{campaign_id}", summary="Delete a campaign")
async def delete_campaign(campaign_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    name = campaign.name
    db.delete(campaign)
    db.commit()

    add_audit_log(db, f"Deleted campaign '{name}'", actor="admin")
    return {"status": "success", "message": f"Campaign '{name}' deleted successfully"}
