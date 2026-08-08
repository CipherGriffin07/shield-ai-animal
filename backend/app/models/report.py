from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportStatus(str, enum.Enum):
    SUBMITTED = "Report Submitted"
    AI_ASSESSMENT_COMPLETED = "AI Assessment Completed"
    VOLUNTEER_ASSIGNED = "Volunteer Assigned"
    VOLUNTEER_EN_ROUTE = "Volunteer En Route"
    VOLUNTEER_REACHED = "Volunteer Reached Location"
    ANIMAL_RESCUED = "Animal Rescued"
    HOSPITAL_REACHED = "Veterinary Centre Reached"
    UNDER_TREATMENT = "Under Treatment"
    RECOVERED = "Recovered"
    CASE_CLOSED = "Case Closed"


class SeverityLevel(str, enum.Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    display_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)  # e.g. SHIELD-2026-0001

    reporter_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reporter_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)

    animal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("animals.id"), nullable=True)
    animal_type: Mapped[str] = mapped_column(String(50), nullable=False)

    landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    video_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    voice_note_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # AI assessment (Gemini Vision result, or rule-based fallback)
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), default=SeverityLevel.LOW)
    priority_score: Mapped[int] = mapped_column(Integer, default=0)

    assigned_volunteer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("volunteer_profiles.id"), nullable=True)
    assigned_ngo_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ngo_profiles.id"), nullable=True)
    assigned_hospital_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("hospitals.id"), nullable=True)

    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.SUBMITTED)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reporter = relationship("User", back_populates="reports", foreign_keys=[reporter_id])
    animal = relationship("Animal", back_populates="report")
    tracking_events = relationship("TrackingEvent", back_populates="report", cascade="all, delete-orphan", order_by="TrackingEvent.created_at")
