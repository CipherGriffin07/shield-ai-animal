from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)

    # Comma-separated list of animal types the volunteer is experienced with, e.g. "Dog,Cat,Bird"
    animal_experience: Mapped[str] = mapped_column(String(255), default="")
    has_vehicle: Mapped[bool] = mapped_column(Boolean, default=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_location_update: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    total_rescues_completed: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=5.0)

    ngo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ngo_profiles.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="volunteer_profile")
    ngo = relationship("NGOProfile", back_populates="volunteers")

    def experience_list(self) -> list[str]:
        return [a.strip() for a in self.animal_experience.split(",") if a.strip()]
