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
                "question_en": entry.question_en,
                "answer_en": entry.answer_en,
                "question_ml": entry.question_ml,
                "answer_ml": entry.answer_ml,
                "embedding": _vectorize(_entry_text(entry)),
            }
        )
    return index


def refresh_index(db: Session) -> None:
    """Refresh the RAG index from the database."""
    global _INDEX
    _INDEX = _build_index(db)
    print(f"[RAG] Index refreshed from database, containing {len(_INDEX)} entries.")


# Global index - will be populated from database
_INDEX: List[Dict[str, Any]] = []

def _get_index(db: Session) -> List[Dict[str, Any]]:
    """Retrieve the cached RAG index, populating it if empty."""
    global _INDEX
    if not _INDEX:
        _INDEX = _build_index(db)
    return _INDEX


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
    index = _get_index(db)
    if index:
        query_embedding = _vectorize(query)
        scored: List[Dict[str, Any]] = []
        for doc in index:
            score = _cosine_similarity(query_embedding, doc["embedding"])
            if score > 0:
                scored.append({"score": score, "id": doc["id"]})
        
        scored.sort(key=lambda item: item["score"], reverse=True)
        
        matching_ids = [item["id"] for item in scored[:top_k]]
        if matching_ids:
            current_entries = db.query(Knowledge).filter(Knowledge.id.in_(matching_ids)).all()
            # Order them by score
            entry_map = {e.id: e for e in current_entries}
            for m_id in matching_ids:
                if m_id in entry_map:
                    docs.append(entry_map[m_id])

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
    query: str, db: Session, language: str = "en", top_k: int = 2, chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """RAG answer with optional OpenAI/Sarvam enhancement when API keys are configured."""
    # Check if the query is a basic greeting/conversational filler.
    # If not filler and not relevant, immediately return deflection (zero-latency out-of-scope bypass)
    from app.services.voice import is_query_relevant_to_bridgeon
    
    def is_conversational_filler(q: str) -> bool:
        if not q:
            return True
        q_clean = q.lower().strip()
        fillers = {
            "hello", "hi", "hey", "hallo", "helo", "yes", "no", "ok", "okay", "yep", "yeah", "sure",
            "thanks", "thank you", "bye", "goodbye", "exit", "quit", "welcome", "please",
            "namaskaram", "namaskaaram", "ഹലോ", "നമസ്കാരം", "അതെ", "ശരി", "നന്ദി", "ബൈ",
            "താങ്ക്സ്", "താങ്ക് യു", "ഒന്നുമില്ല", "മതി", "പോകട്ടെ"
        }
        import re
        words = [w for w in re.findall(r"\w+", q_clean) if w]
        if not words:
            return True
        return all(w in fillers for w in words)
        
    if not is_conversational_filler(query) and not is_query_relevant_to_bridgeon(query):
        import re
        q_words = [w for w in re.findall(r"\w+", query.lower()) if w]
        if len(q_words) >= 3:
            print(f"[RAG] Out-of-scope query '{query}' detected. Bypassing LLM immediately.")
            from app.core.config import settings
            if not (settings.openai_configured or settings.sarvam_configured or settings.gemma_configured):
                return ""
            if language == "ml":
                return "എനിക്ക് ബ്രിഡ്ജിയോൺ കോഴ്സുകളെക്കുറിച്ചുള്ള ചോദ്യങ്ങൾക്ക് മാത്രമേ മറുപടി നൽകാൻ സാധിക്കൂ. കൂടുതൽ സഹായത്തിനായി ഞാൻ നിങ്ങളെ കൗൺസിലറുമായി ബന്ധിപ്പിക്കാം."
            return "I can only help you with questions about Bridgeon courses. I can connect you to our training counselor for further assistance."

    # First, check if we have an exact or high-confidence FAQ match in the database to bypass the LLM
    index = _get_index(db)
    if index:
        query_embedding = _vectorize(query)
        scored = []
        for doc in index:
            score = _cosine_similarity(query_embedding, doc["embedding"])
            # Threshold of 0.65 represents a very strong match for key terms
            if score > 0.65:
                scored.append((score, doc))
        
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            best_score, best_doc = scored[0]
            print(f"[RAG] High-confidence FAQ match found (score={best_score:.2f}), bypassing LLM to decrease thinking time.")
            if language == "ml":
                return best_doc["answer_ml"] or best_doc["answer_en"] or ""
            return best_doc["answer_en"] or best_doc["answer_ml"] or ""

    # Otherwise, proceed with full RAG + LLM enhancement
    docs = retrieve_relevant_docs(query, db, top_k=top_k)
    context = ""
    if docs:
        context = _build_context(docs, language)

    if not context:
        from app.services.voice import search_company_info, is_query_relevant_to_bridgeon
        if is_query_relevant_to_bridgeon(query):
            print(f"[RAG] No local context found, running web search for query: {query}")
            search_results = search_company_info(query)
            if search_results and "Error searching the web" not in search_results and "No results found" not in search_results:
                context = f"Web Search Results:\n{search_results}"
        else:
            print(f"[RAG] Query '{query}' is out of scope. Skipping web search.")

    from app.core.config import settings
    from app.services.voice import enhance_rag_answer, sarvam_enhance_rag_answer, gemma_enhance_rag_answer

    # If context is empty, only proceed if LLMs are configured. Otherwise exit.
    if not context or not context.strip():
        if not (settings.openai_configured or settings.sarvam_configured or settings.gemma_configured):
            return ""
        context = ""

    # 1. Try Gemma RAG enhancement first if configured
    if settings.gemma_configured:
        try:
            enhanced = await gemma_enhance_rag_answer(query, context, language, chat_history)
            if enhanced:
                return enhanced
        except Exception as e:
            print(f"[RAG] Gemma enhancement failed ({type(e).__name__}), trying OpenAI fallback.")

    # 2. Try OpenAI RAG enhancement
    if settings.openai_configured:
        try:
            enhanced = await enhance_rag_answer(query, context, language, chat_history)
            if enhanced:
                return enhanced
        except Exception as e:
            print(f"[RAG] OpenAI enhancement failed ({type(e).__name__}), trying Sarvam fallback.")

    # 3. Fall back to Sarvam AI LLM RAG enhancement
    if settings.sarvam_configured:
        try:
            enhanced = await sarvam_enhance_rag_answer(query, context, language, chat_history)
            if enhanced:
                return enhanced
        except Exception as e:
            print(f"[RAG] Sarvam LLM enhancement failed: {e}")

    if not context:
        return ""

    if len(context.split("\n")) == 1:
        return f"Based on our knowledge base: {context}"
    return f"Based on our knowledge base: {context.replace(chr(10), ' ')}"
