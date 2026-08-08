from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.report import ReportStatus, SeverityLevel


class AIAnalysisResult(BaseModel):
    animal: str
    injury: str
    visible_signs: str
    severity: SeverityLevel
    confidence: float
    bleeding_detected: bool
    fracture_suspected: bool
    first_aid: str
    recommendation: str
    disclaimer: str
    source: str  # "gemini_vision" | "rule_based_fallback"


class AssignedVolunteerOut(BaseModel):
    id: str
    name: str
    phone: str | None = None
    distance_km: float
    has_vehicle: bool


class ReportOut(BaseModel):
    id: str
    display_id: str
    reporter_name: str
    phone: str
    animal_type: str
    landmark: str | None
    description: str
    image_url: str
    latitude: float
    longitude: float
    analysis: AIAnalysisResult
    priority_score: int
    severity: SeverityLevel
    assigned_volunteer: AssignedVolunteerOut | None = None
    status: ReportStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
    note: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class TrackingEventOut(BaseModel):
    status: str
    note: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
