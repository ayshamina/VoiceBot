"""
FAQ knowledge base endpoints for Phase 4 (Database-backed).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.core.models import Knowledge
from app.core.metrics import record_event

router = APIRouter()


class KnowledgeEntry(BaseModel):
    id: int
    question_en: str
    answer_en: str
    question_ml: Optional[str]
    answer_ml: Optional[str]
    category: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class KnowledgeCreate(BaseModel):
    question_en: str = Field(..., description="English FAQ question")
    answer_en: str = Field(..., description="English FAQ answer")
    question_ml: str = Field('', description="Malayalam FAQ question")
    answer_ml: str = Field('', description="Malayalam FAQ answer")
    category: str = Field('General', description="Knowledge category")


class KnowledgeUpdate(BaseModel):
    question_en: Optional[str] = None
    answer_en: Optional[str] = None
    question_ml: Optional[str] = None
    answer_ml: Optional[str] = None
    category: Optional[str] = None


def _match_score(query: str, entry: Knowledge) -> int:
    """Calculate relevance score for a knowledge entry."""
    text = f"{entry.question_en} {entry.answer_en} {entry.question_ml or ''} {entry.answer_ml or ''}".lower()
    query_lower = query.lower()
    if query_lower in text:
        return 10
    return sum(1 for token in query_lower.split() if token and token in text)


def find_matching_entries(query: str, db: Session) -> List[Knowledge]:
    """Find knowledge entries matching a query."""
    if not query:
        return []
    
    entries = db.query(Knowledge).all()
    scored = [(entry, _match_score(query, entry)) for entry in entries]
    scored = [(entry, score) for entry, score in scored if score > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [entry for entry, _ in scored]


@router.get("/rag", response_model=List[KnowledgeEntry], summary="Search knowledge using prototype retrieval")
async def rag_search(q: str = Query(..., description="Text to retrieve relevant knowledge entries"), db: Session = Depends(get_db)):
    """Retrieve relevant docs using RAG."""
    from app.core.rag import retrieve_relevant_docs
    return retrieve_relevant_docs(q, db)


@router.get("", response_model=List[KnowledgeEntry], summary="List knowledge entries")
async def list_knowledge(q: Optional[str] = Query(None, description="Search query for FAQ entries"), db: Session = Depends(get_db)):
    """List all knowledge entries, optionally filtered by search query."""
    if q:
        entries = find_matching_entries(q, db)
    else:
        entries = db.query(Knowledge).all()
    return entries


@router.post("", response_model=KnowledgeEntry, summary="Create a knowledge entry")
async def create_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    """Create a new knowledge entry."""
    entry = Knowledge(
        question_en=payload.question_en,
        answer_en=payload.answer_en,
        question_ml=payload.question_ml or None,
        answer_ml=payload.answer_ml or None,
        category=payload.category,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    # Refresh RAG index
    from app.core.rag import refresh_index
    refresh_index(db)
    
    # Record event
    record_event("knowledge_created", "knowledge", entry.id, db)
    
    return entry


@router.get("/search", response_model=List[KnowledgeEntry], summary="Search knowledge entries")
async def search_knowledge(q: str = Query(..., description="Text to search for matching FAQ entries"), db: Session = Depends(get_db)):
    """Search for knowledge entries."""
    entries = find_matching_entries(q, db)
    return entries


@router.get("/{entry_id}", response_model=KnowledgeEntry, summary="Get a knowledge entry")
async def get_knowledge(entry_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific knowledge entry by ID."""
    entry = db.query(Knowledge).filter(Knowledge.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry


@router.put("/{entry_id}", response_model=KnowledgeEntry, summary="Update a knowledge entry")
async def update_knowledge(entry_id: int, payload: KnowledgeUpdate, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    """Update a knowledge entry."""
    entry = db.query(Knowledge).filter(Knowledge.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    # Update fields that were provided
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(entry, field, value)
    
    entry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    
    # Refresh RAG index
    from app.core.rag import refresh_index
    refresh_index(db)
    
    # Record event
    record_event("knowledge_updated", "knowledge", entry.id, db)
    
    return entry


@router.delete("/{entry_id}", summary="Delete a knowledge entry")
async def delete_knowledge(entry_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    """Delete a knowledge entry."""
    entry = db.query(Knowledge).filter(Knowledge.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    question = entry.question_en
    db.delete(entry)
    db.commit()
    
    # Refresh RAG index
    from app.core.rag import refresh_index
    refresh_index(db)
    
    # Record event
    record_event("knowledge_deleted", "knowledge", entry_id, db)
    
    return {"status": "success", "deleted_id": entry_id}


from fastapi import UploadFile, File
import shutil
import tempfile
import os
from app.services.pdf_ingest import ingest_pdf

@router.post("/upload", summary="Upload a PDF document to knowledge base")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin)
):
    """Upload and ingest a PDF document into the vector database."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    temp_file_path = None
    try:
        # Create a temporary file to save the uploaded content
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Call the ingest PDF service
        ingest_pdf(temp_file_path)
        
        # Record event
        record_event("pdf_uploaded", "knowledge", 0, db)
        
        return {"status": "success", "message": f"Successfully ingested {file.filename}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass




