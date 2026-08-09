"""
Database engine, session factory, and declarative base for SHIELD AI.
Uses SQLAlchemy so the same model definitions can run against SQLite
locally and PostgreSQL/MySQL in production.
"""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


database_url = settings.database_url

if os.getenv("VERCEL") and database_url.startswith("sqlite"):
    database_url = "sqlite:////tmp/shield.db"


connect_args = (
    {"check_same_thread": False}
    if database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    database_url,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    """Yield a database session and always close it."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables that do not already exist."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)