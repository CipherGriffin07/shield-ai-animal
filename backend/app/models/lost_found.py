from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LostFoundType(str, enum.Enum):
    LOST = "lost"
    FOUND = "found"


class LostFoundStatus(str, enum.Enum):
    OPEN = "open"
    MATCHED = "matched"
    REUNITED = "reunited"
    CLOSED = "closed"


class LostFoundPost(Base):
    __tablename__ = "lost_found_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    posted_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    post_type: Mapped[LostFoundType] = mapped_column(Enum(LostFoundType), nullable=False)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    color_markings: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Perceptual/feature hash used for AI similarity matching against other posts
    image_signature: Mapped[str | None] = mapped_column(String(128), nullable=True)

    last_seen_landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[LostFoundStatus] = mapped_column(Enum(LostFoundStatus), default=LostFoundStatus.OPEN)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    matches_as_source = relationship(
        "LostFoundMatch", back_populates="source_post",
        foreign_keys="LostFoundMatch.source_post_id", cascade="all, delete-orphan",
    )


class LostFoundMatch(Base):
    """A candidate match between a 'lost' post and a 'found' post,
    scored by the AI similarity engine."""
    __tablename__ = "lost_found_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    source_post_id: Mapped[str] = mapped_column(String(36), ForeignKey("lost_found_posts.id"), nullable=False)
    candidate_post_id: Mapped[str] = mapped_column(String(36), ForeignKey("lost_found_posts.id"), nullable=False)

    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 - 1.0
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    owner_notified: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source_post = relationship("LostFoundPost", back_populates="matches_as_source", foreign_keys=[source_post_id])
