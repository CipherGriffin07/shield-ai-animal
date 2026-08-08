from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.adoption import AdoptionStatus, ApplicationStatus
from app.models.lost_found import LostFoundStatus, LostFoundType


# ---------- Chat ----------
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    source: str  # "gemini" | "rule_based_fallback"


# ---------- Lost & Found ----------
class LostFoundPostOut(BaseModel):
    id: str
    post_type: LostFoundType
    animal_type: str
    breed: str | None
    color_markings: str | None
    description: str
    image_url: str
    last_seen_landmark: str | None
    latitude: float
    longitude: float
    contact_phone: str
    status: LostFoundStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class LostFoundMatchOut(BaseModel):
    candidate_post: LostFoundPostOut
    similarity_score: float
    distance_km: float


# ---------- Adoption ----------
class AdoptionListingOut(BaseModel):
    id: str
    animal_id: str
    title: str
    story: str | None
    temperament_tags: list[str]
    status: AdoptionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class AdoptionQuestionnaire(BaseModel):
    home_type: str          # apartment | house_with_yard | farm
    has_other_pets: bool
    has_children: bool
    daily_hours_available: int
    experience_level: str   # beginner | intermediate | experienced
    preferred_temperament: list[str] = Field(default_factory=list)


class AdoptionApplicationCreate(BaseModel):
    listing_id: str
    questionnaire: AdoptionQuestionnaire


class AdoptionApplicationOut(BaseModel):
    id: str
    listing_id: str
    applicant_id: str
    compatibility_score: float
    status: ApplicationStatus
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Analytics ----------
class DashboardStats(BaseModel):
    total_reports: int
    critical_reports: int
    active_rescues: int
    completed_rescues: int
    total_volunteers: int
    total_ngos: int
    average_response_minutes: float | None


class TimeseriesPoint(BaseModel):
    period: str
    count: int


class HeatmapPoint(BaseModel):
    latitude: float
    longitude: float
    weight: int
