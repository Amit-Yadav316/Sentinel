"""SQLAlchemy 2.0 engine + session setup.

Uses SQLite (file-backed) instead of Postgres+pgvector so the app runs with zero
external services. Models are DB-agnostic; the only Postgres-specific feature we
skip is pgvector — procurement runs an in-process cosine search instead
(see agents/procurement.py). Swap ``DATABASE_URL`` for Postgres in production.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# check_same_thread=False so the FastAPI threadpool + websocket loop can share it.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Called on startup and by the seed script."""
    from app.models import Base  # noqa: WPS433 — avoid circular import at module load

    Base.metadata.create_all(bind=engine)
