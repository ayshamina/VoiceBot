import os
from pathlib import Path

from pypdf import PdfReader


def ingest_pdf(file_path: str, collection_name: str = "bridgeon_docs") -> None:
    """Extract text from a PDF, split into chunks, embed, and store in Chroma.

    The collection is persisted under `backend/data/vectorstore/{collection_name}`.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import Chroma
    except ImportError:
        raise ImportError(
            "LangChain and Chroma dependencies are required for PDF ingestion. "
            "Please run: pip install langchain-text-splitters langchain-openai langchain-community chromadb"
        )
    # 1️⃣ Extract raw text from PDF pages
    reader = PdfReader(file_path)
    text_list = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_list.append(text)
    raw_text = "\n\n".join(text_list)

    if not raw_text.strip():
        raise ValueError("The PDF file does not contain extractable text.")

    # 2️⃣ Chunk the text for better retrieval
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(raw_text)

    # 3️⃣ Choose embedding backend (free local HuggingFace by default)
    if os.getenv("USE_OPENAI_EMBEDDINGS", "").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    else:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 4️⃣ Persist to Chroma (creates/opens the collection)
    store_path = Path(__file__).resolve().parents[3] / "data" / "vectorstore" / collection_name
    os.makedirs(store_path, exist_ok=True)
    vector_db = Chroma.from_texts(chunks, embeddings, persist_directory=str(store_path))
    if hasattr(vector_db, "persist"):
        vector_db.persist()

