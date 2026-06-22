"""
Local RAG prototype for Phase 8 (Database-backed).
Uses a lightweight in-memory semantic scorer over the knowledge base.
"""
import math
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from app.core.models import Knowledge


_STOP_WORDS = {
    "what", "is", "a", "an", "the", "of", "in", "on", "at", "for", "to", "with", 
    "and", "or", "it", "this", "that", "these", "those", "your", "my", "me", "i", 
    "you", "we", "they", "he", "she", "do", "does", "did", "are", "was", "were", "be", "been"
}

def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words, filtering out common stop words."""
    tokens = [token for token in re.findall(r"\w+", text.lower()) if token]
    return [t for t in tokens if t not in _STOP_WORDS]


def _vectorize(text: str) -> Dict[str, int]:
    """Convert text to a simple bag-of-words vector."""
    embedding: Dict[str, int] = {}
    for token in _tokenize(text):
        embedding[token] = embedding.get(token, 0) + 1
    return embedding


def _dot(a: Dict[str, int], b: Dict[str, int]) -> int:
    """Compute dot product of two vectors."""
    return sum(a.get(term, 0) * b.get(term, 0) for term in a)


def _magnitude(vec: Dict[str, int]) -> float:
    """Compute magnitude (L2 norm) of a vector."""
    return math.sqrt(sum(value * value for value in vec.values()))


def _cosine_similarity(a: Dict[str, int], b: Dict[str, int]) -> float:
    """Compute cosine similarity between two vectors."""
    denom = _magnitude(a) * _magnitude(b)
    if denom == 0:
        return 0.0
    return _dot(a, b) / denom


def _entry_text(entry: Knowledge) -> str:
    """Extract all text from a knowledge entry for embedding."""
    return " ".join(
        [
            entry.question_en or "",
            entry.answer_en or "",
            entry.question_ml or "",
            entry.answer_ml or "",
        ]
    )


def _build_index(db: Session) -> List[Dict[str, Any]]:
    """Build RAG index from knowledge base entries."""
    index: List[Dict[str, Any]] = []
    entries = db.query(Knowledge).all()
    
    for entry in entries:
        index.append(
            {
                "id": entry.id,
                "entry": entry,
                "embedding": _vectorize(_entry_text(entry)),
            }
        )
    return index


def refresh_index(db: Session) -> None:
    """Refresh the RAG index from the database."""
    global _INDEX
    _INDEX = _build_index(db)


# Global index - will be populated from database
_INDEX: List[Dict[str, Any]] = []


from pathlib import Path

def retrieve_relevant_docs(query: str, db: Session, top_k: int = 3) -> List[Knowledge]:
    """Retrieve top-k relevant documents for a query, merging DB FAQs and Chroma vector store."""
    if not query:
        return []

    # 1. Fetch from Vector Database
    from app.core.vectorstore import query_documents
    vector_matches = query_documents(query, n_results=top_k)
    
    docs: List[Knowledge] = []
    
    # Convert vector matches to mock Knowledge objects
    for i, doc in enumerate(vector_matches):
        source = Path(doc.metadata.get("source", "document")).name if doc.metadata else "document"
        has_ml = bool(re.search(r"[\u0d00-\u0d7f]", doc.page_content))
        k = Knowledge(
            id=-100 - i,
            question_en=f"Document snippet from {source}",
            answer_en=doc.page_content,
            question_ml=f"{source} രേഖ",
            answer_ml=doc.page_content if has_ml else None,
            category="Vector Document"
        )
        docs.append(k)

    # 2. Fetch from Database (FAQ entries)
    index = _build_index(db)
    if index:
        query_embedding = _vectorize(query)
        scored: List[Dict[str, Any]] = []
        for doc in index:
            score = _cosine_similarity(query_embedding, doc["embedding"])
            if score > 0:
                scored.append({"score": score, "entry": doc["entry"]})
        
        scored.sort(key=lambda item: item["score"], reverse=True)
        for item in scored[:top_k]:
            docs.append(item["entry"])

    return docs[:top_k]


def _build_context(docs: List[Knowledge], language: str) -> str:
    answers: List[str] = []
    for entry in docs:
        if language == "ml":
            answers.append(entry.answer_ml or entry.answer_en or "")
        else:
            answers.append(entry.answer_en or entry.answer_ml or "")
    return "\n".join(answer.strip() for answer in answers if answer and answer.strip())


def retrieve_grounded_answer(query: str, db: Session, language: str = "en", top_k: int = 2) -> str:
    """Retrieve a grounded answer from the knowledge base."""
    docs = retrieve_relevant_docs(query, db, top_k=top_k)
    if not docs:
        return ""

    context = _build_context(docs, language)
    if not context:
        return ""

    if len(context.split("\n")) == 1:
        return f"Based on our knowledge base: {context}"

    return f"Based on our knowledge base: {context.replace(chr(10), ' ')}"


async def retrieve_grounded_answer_async(
    query: str, db: Session, language: str = "en", top_k: int = 2
) -> str:
    """RAG answer with optional OpenAI/Sarvam enhancement when API keys are configured."""
    docs = retrieve_relevant_docs(query, db, top_k=top_k)
    context = ""
    if docs:
        context = _build_context(docs, language)

    if not context:
        from app.services.voice import search_company_info
        print(f"[RAG] No local context found, running web search for query: {query}")
        search_results = search_company_info(query)
        if search_results and "Error searching the web" not in search_results and "No results found" not in search_results:
            context = f"Web Search Results:\n{search_results}"

    from app.core.config import settings
    from app.services.voice import enhance_rag_answer, sarvam_enhance_rag_answer

    # If context is empty, only proceed if LLMs are configured. Otherwise exit.
    if not context or not context.strip():
        if not (settings.openai_configured or settings.sarvam_configured):
            return ""
        context = ""

    # 1. Try OpenAI RAG enhancement first
    if settings.openai_configured:
        try:
            enhanced = await enhance_rag_answer(query, context, language)
            if enhanced:
                return enhanced
        except Exception as e:
            print(f"[RAG] OpenAI enhancement failed ({type(e).__name__}), trying Sarvam fallback.")

    # 2. Fall back to Sarvam AI LLM RAG enhancement
    if settings.sarvam_configured:
        try:
            enhanced = await sarvam_enhance_rag_answer(query, context, language)
            if enhanced:
                return enhanced
        except Exception as e:
            print(f"[RAG] Sarvam LLM enhancement failed: {e}")

    if not context:
        return ""

    if len(context.split("\n")) == 1:
        return f"Based on our knowledge base: {context}"
    return f"Based on our knowledge base: {context.replace(chr(10), ' ')}"
