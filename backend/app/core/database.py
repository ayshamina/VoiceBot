"""
Database configuration and session management for SQLAlchemy.
Supports both PostgreSQL (production) and SQLite (development).
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from app.core.config import settings

# Detect if using SQLite
_is_sqlite = settings.DATABASE_URL.startswith("sqlite:")

# Create engine with connection pooling (disabled for SQLite)
engine_kwargs: dict = {
    "echo": settings.DATABASE_ECHO,
}

if _is_sqlite:
    # SQLite doesn't support connection pooling or pool_pre_ping
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool
else:
    # PostgreSQL connection pooling
    engine_kwargs["pool_pre_ping"] = True  # Verify connections before using them
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Enable foreign keys for SQLite
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for all models
Base = declarative_base()


def get_db() -> Session:
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    db_type = "SQLite" if _is_sqlite else "PostgreSQL"
    print(f"[DB] All tables created successfully ({db_type}).")
