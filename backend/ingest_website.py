"""
Script to ingest the Bridgeon website content into the bot's Chroma vector store.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path to allow imports
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

from app.services.url_ingest import ingest_url

async def main():
    urls = [
        "https://bridgeon.in/",
        "https://bridgeon.in/about"
    ]
    
    print("[IngestScript] Starting website content ingestion...")
    for url in urls:
        print(f"[IngestScript] Ingesting: {url}...")
        try:
            await ingest_url(url)
            print(f"[IngestScript] Successfully ingested: {url}")
        except Exception as e:
            print(f"[IngestScript] Error ingesting {url}: {e}", file=sys.stderr)
            
    print("[IngestScript] Ingestion process completed!")

if __name__ == "__main__":
    asyncio.run(main())
