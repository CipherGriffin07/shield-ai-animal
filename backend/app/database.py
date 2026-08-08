"""
Database engine, session factory, and declarative base for SHIELD AI.

Uses SQLAlchemy so the same model definitions can run against SQLite
today and be pointed at Postgres/MySQL later by changing DATABASE_URL
alone - no model or route code needs to change.
"""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    """FastAPI dependency that yields a database session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables that don't already exist. Import models first so
    they register themselves on Base.metadata before this is called."""
    from app import models  # noqa: F401  (ensures all model modules are imported)
    Base.metadata.create_all(bind=engine)
