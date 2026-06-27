import os
from pathlib import Path
import re
from html.parser import HTMLParser
import httpx

async def ingest_url(url: str, collection_name: str = "bridgeon_docs") -> None:
    """Fetch content from a URL, extract text, chunk, embed, and store in Chroma.

    The collection is persisted under `backend/data/vectorstore/{collection_name}`.
    """
    # 1. Fetch HTML content
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html_content = response.text
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            raise ValueError("This website's security policies (e.g., Cloudflare) block automated scraping. Please try another URL or add the FAQ entries manually.")
        raise ValueError(f"HTTP error {e.response.status_code} occurred while fetching the website.")
    except Exception as e:
        raise ValueError(f"Could not connect to the website: {str(e)}")

    # 2. Extract raw text from HTML, ignoring scripts/styles/navigation/footers
    class HTMLTextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts = []
            self.ignored_tags_depth = 0

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style", "nav", "footer", "header"):
                self.ignored_tags_depth += 1

        def handle_endtag(self, tag):
            if tag in ("script", "style", "nav", "footer", "header"):
                self.ignored_tags_depth = max(0, self.ignored_tags_depth - 1)

        def handle_data(self, data):
            if self.ignored_tags_depth == 0:
                self.text_parts.append(data)

        def get_text(self) -> str:
            text = "\n".join(self.text_parts)
            # Collapse spaces and format newlines
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n+', '\n\n', text)
            return text.strip()

    parser = HTMLTextExtractor()
    parser.feed(html_content)
    raw_text = parser.get_text()

    if not raw_text.strip():
        raise ValueError("The URL does not contain extractable text.")

    # 3. Chunk the text for better retrieval
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import Chroma
    except ImportError:
        raise ImportError(
            "LangChain and Chroma dependencies are required for URL ingestion. "
            "Please run: pip install langchain-text-splitters langchain-openai langchain-community chromadb"
        )

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(raw_text)

    # 4. Choose embedding backend (free local HuggingFace by default)
    if os.getenv("USE_OPENAI_EMBEDDINGS", "").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 5. Persist to Chroma
    store_path = Path(__file__).resolve().parents[2] / "data" / "vectorstore" / collection_name
    os.makedirs(store_path, exist_ok=True)
    
    # Store source metadata so retriever knows the URL origin
    metadatas = [{"source": url} for _ in chunks]
    vector_db = Chroma.from_texts(chunks, embeddings, metadatas=metadatas, persist_directory=str(store_path))
    if hasattr(vector_db, "persist"):
        vector_db.persist()
