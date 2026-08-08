from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VolunteerProfileUpdate(BaseModel):
    animal_experience: list[str] = Field(default_factory=list)
    has_vehicle: bool = False
    years_experience: int = 0
    is_available: bool = True


class VolunteerLocationUpdate(BaseModel):
    latitude: float
    longitude: float


class VolunteerProfileOut(BaseModel):
    id: str
    user_id: str
    animal_experience: list[str]
    has_vehicle: bool
    years_experience: int
    is_available: bool
    latitude: float | None
    longitude: float | None
    total_rescues_completed: int
    rating: float
    created_at: datetime

    model_config = {"from_attributes": True}


class NGOProfileUpdate(BaseModel):
    organization_name: str
    registration_number: str | None = None
    description: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int = 0


class NGOProfileOut(BaseModel):
    id: str
    user_id: str
    organization_name: str
    registration_number: str | None
    description: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    is_verified: bool
    capacity: int
    created_at: datetime

    model_config = {"from_attributes": True}
