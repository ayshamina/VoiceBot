import os
from dotenv import load_dotenv
load_dotenv()
from app.services.pdf_ingest import ingest_pdf

print("Starting direct ingestion test...")
try:
    ingest_pdf("bridgeon_info.pdf")
    print("Direct Ingestion successful!")
except Exception as e:
    print("Ingestion failed with error:", e)
