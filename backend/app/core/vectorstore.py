import os
from pathlib import Path
try:
    from langchain_community.vectorstores import Chroma
    _langchain_available = True
except ImportError:
    _langchain_available = False

VECTORSTORE_DIR = Path(__file__).resolve().parents[2] / "data" / "vectorstore" / "bridgeon_docs"
os.makedirs(VECTORSTORE_DIR.parent, exist_ok=True)

_cached_embeddings = None
_cached_vector_store = None

def get_embeddings():
    """Use free local HuggingFace embeddings by default.
    Set USE_OPENAI_EMBEDDINGS=true in .env to use OpenAI instead."""
    global _cached_embeddings
    if _cached_embeddings is not None:
        return _cached_embeddings

    if not _langchain_available:
        return None
    if os.getenv("USE_OPENAI_EMBEDDINGS", "").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        from langchain_openai import OpenAIEmbeddings
        _cached_embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _cached_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _cached_embeddings

def get_vector_store():
    global _cached_vector_store
    if _cached_vector_store is not None:
        return _cached_vector_store

    if not _langchain_available:
        return None
    embeddings = get_embeddings()
    _cached_vector_store = Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)
    return _cached_vector_store

def query_documents(query: str, n_results: int = 5):
    """Perform a similarity search using LangChain's Chroma wrapper.

    Returns:
        List of matching Document objects.
    """
    try:
        vector_db = get_vector_store()
        docs = vector_db.similarity_search(query, k=n_results)
        return docs
    except Exception as e:
        print(f"[VectorStore] Error querying documents: {e}")
        return []

