import os
from pathlib import Path
try:
    from langchain_community.vectorstores import Chroma
    _langchain_available = True
except ImportError:
    _langchain_available = False

VECTORSTORE_DIR = Path(__file__).resolve().parents[2] / "data" / "vectorstore" / "bridgeon_docs"
os.makedirs(VECTORSTORE_DIR.parent, exist_ok=True)

def get_embeddings():
    """Use free local HuggingFace embeddings by default.
    Set USE_OPENAI_EMBEDDINGS=true in .env to use OpenAI instead."""
    if not _langchain_available:
        return None
    if os.getenv("USE_OPENAI_EMBEDDINGS", "").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-large")
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_vector_store():
    if not _langchain_available:
        return None
    embeddings = get_embeddings()
    return Chroma(persist_directory=str(VECTORSTORE_DIR), embedding_function=embeddings)

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

