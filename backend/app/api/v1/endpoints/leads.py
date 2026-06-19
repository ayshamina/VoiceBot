"""
Lead capture endpoints for Phase 5 (Database-backed).
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.core.models import Lead
from app.core.metrics import record_event

router = APIRouter()


class LeadEntry(BaseModel):
    id: int
    name: str
    phone: str
    course: str
    consent_whatsapp: Optional[bool]
    language: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True



class LeadCreate(BaseModel):
    name: str = Field(..., description="Lead name")
    phone: str = Field(..., description="Phone number of the lead")
    course: str = Field(..., description="Interested course or training track")
    consent_whatsapp: Optional[bool] = Field(None, description="Consent to WhatsApp follow-up")
    language: str = Field('en', description="Preferred language for the lead")
    source: str = Field('bot', description="Source of lead capture")


def _normalize_phone(phone: str) -> str:
    """Normalize and validate phone number."""
    cleaned = "".join(filter(str.isdigit, phone))
    if len(cleaned) < 5:
        raise HTTPException(status_code=400, detail="Phone number is too short")
    return cleaned


def get_lead_count(db: Session) -> int:
    """Get total number of leads."""
    return db.query(Lead).count()


def create_lead_record(
    db: Session,
    name: str,
    phone: str,
    course: str,
    consent_whatsapp: Optional[bool] = None,
    language: str = 'en',
    source: str = 'bot',
) -> Lead:
    """Create a new lead record."""
    clean_phone = _normalize_phone(phone)
    lead = Lead(
        name=name.strip(),
        phone=clean_phone,
        course=course.strip(),
        consent_whatsapp=consent_whatsapp,
        language=language or 'en',
        source=source,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    # Record event
    record_event("lead_created", "lead", lead.id, db)
    
    # Dispatch WhatsApp, SMS, and Email notifications asynchronously
    import asyncio
    from app.services.messaging import dispatch_lead_notifications
    try:
        asyncio.create_task(dispatch_lead_notifications(lead, db))
    except Exception:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(dispatch_lead_notifications(lead, db))
            else:
                loop.run_until_complete(dispatch_lead_notifications(lead, db))
        except Exception:
            pass
    
    return lead


@router.get("", response_model=list[LeadEntry], summary="List captured leads")
async def list_leads(db: Session = Depends(get_db), _: str = Depends(require_admin)):
    """List all captured leads (admin only)."""
    leads = db.query(Lead).all()
    return leads


@router.post("", response_model=LeadEntry, summary="Create a lead record")
async def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead record."""
    lead = create_lead_record(
        db=db,
        name=payload.name,
        phone=payload.phone,
        course=payload.course,
        consent_whatsapp=payload.consent_whatsapp,
        language=payload.language,
        source=payload.source,
    )
    
    return lead


@router.get("/{lead_id}", response_model=LeadEntry, summary="Get a lead record")
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific lead record by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.delete("/{lead_id}", summary="Delete a lead record")
async def delete_lead(lead_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    """Delete a lead record (admin only)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db.delete(lead)
    db.commit()
    
    # Record event
    record_event("lead_deleted", "lead", lead_id, db)
    
    return {"status": "success", "deleted_id": lead_id}
