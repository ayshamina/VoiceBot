"""
Bridgeon Voice Call Assistant — Backend
Main application entry point (Phase 1 Scaffold + Database Backend)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.init_db import init_sample_data
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler -- startup and shutdown logic."""
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    
    # Initialize database on startup
    try:
        print("[DB] Initializing database...")
        init_db()
        init_sample_data()
        print("[DB] Database initialized successfully!")
    except Exception as e:
        print(f"[DB] Error initializing database: {e}")
        print(f"[DB] Make sure PostgreSQL is running and DATABASE_URL is correct in .env")
    
    yield
    print("[STOP] Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered, telephony-integrated voice bot for Bridgeon Skillversity. "
        "Handles inbound/outbound calls, multilingual support (English + Malayalam), "
        "lead capture, admin dashboard, and RAG-powered knowledge retrieval."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "database": "PostgreSQL (configured)",
    }


# ── Server Startup ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
