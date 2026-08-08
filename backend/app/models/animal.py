from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnimalSpecies(str, enum.Enum):
    DOG = "Dog"
    CAT = "Cat"
    BIRD = "Bird"
    COW = "Cow"
    GOAT = "Goat"
    SNAKE = "Snake"
    OTHER = "Other"


class AnimalStatus(str, enum.Enum):
    UNDER_TREATMENT = "under_treatment"
    RECOVERED = "recovered"
    UP_FOR_ADOPTION = "up_for_adoption"
    ADOPTED = "adopted"
    RELEASED = "released"
    DECEASED = "deceased"


class Animal(Base):
    """Canonical record for an individual animal, created once a report
    is confirmed and carried through treatment, recovery, and possibly
    adoption or release."""
    __tablename__ = "animals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    species: Mapped[AnimalSpecies] = mapped_column(Enum(AnimalSpecies), default=AnimalSpecies.OTHER)
    breed: Mapped[str | None] = mapped_column(String(120), nullable=True)
    estimated_age_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color_markings: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    status: Mapped[AnimalStatus] = mapped_column(Enum(AnimalStatus), default=AnimalStatus.UNDER_TREATMENT)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    report = relationship("Report", back_populates="animal", uselist=False)
    adoption_listing = relationship("AdoptionListing", back_populates="animal", uselist=False)
