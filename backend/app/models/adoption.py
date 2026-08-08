from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AdoptionStatus(str, enum.Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    ADOPTED = "adopted"
    WITHDRAWN = "withdrawn"


class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AdoptionListing(Base):
    __tablename__ = "adoption_listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    animal_id: Mapped[str] = mapped_column(String(36), ForeignKey("animals.id"), unique=True, nullable=False)
    listed_by_ngo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ngo_profiles.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    story: Mapped[str | None] = mapped_column(Text, nullable=True)
    temperament_tags: Mapped[str] = mapped_column(String(255), default="")  # comma-separated: "calm,child-friendly"
    status: Mapped[AdoptionStatus] = mapped_column(Enum(AdoptionStatus), default=AdoptionStatus.AVAILABLE)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    animal = relationship("Animal", back_populates="adoption_listing")
    applications = relationship("AdoptionApplication", back_populates="listing", cascade="all, delete-orphan")


class AdoptionApplication(Base):
    __tablename__ = "adoption_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    listing_id: Mapped[str] = mapped_column(String(36), ForeignKey("adoption_listings.id"), nullable=False)
    applicant_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Compatibility questionnaire answers, stored as JSON text
    questionnaire_json: Mapped[str] = mapped_column(Text, nullable=False)
    compatibility_score: Mapped[float] = mapped_column(default=0.0)  # 0-100, from AI recommendation engine

    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.SUBMITTED)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing = relationship("AdoptionListing", back_populates="applications")
