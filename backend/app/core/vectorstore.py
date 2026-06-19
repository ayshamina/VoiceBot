import os
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# Directory for vector store (under backend/data)
VECTORSTORE_DIR = Path(__file__).resolve().parents[2] / "data" / "vectorstore" / "bridgeon_docs"
os.makedirs(VECTORSTORE_DIR.parent, exist_ok=True)

def get_embeddings():
    """Use free local HuggingFace embeddings by default.
    Set USE_OPENAI_EMBEDDINGS=true in .env to use OpenAI instead."""
    if os.getenv("USE_OPENAI_EMBEDDINGS", "").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model="text-embedding-3-large")
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_vector_store() -> Chroma:
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

