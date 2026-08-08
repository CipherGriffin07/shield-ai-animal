"""
Volunteer auto-matching engine.

Scores every available volunteer against a report using:
  - animal-experience match       (weight 35)
  - vehicle availability          (weight 25)
  - proximity                     (weight up to 40, decaying with distance)
  - track record (rating)         (weight up to 10)

and returns the highest-scoring candidate. This replaces the MVP's
hardcoded VOLUNTEERS list with real volunteer_profiles rows from the
database, so results change as volunteers sign up, go offline, or
update their location.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.volunteer import VolunteerProfile
from app.utils.geo import haversine_km


def find_best_volunteer(db: Session, animal_type: str, latitude: float, longitude: float) -> VolunteerProfile | None:
    candidates = (
        db.query(VolunteerProfile)
        .filter(VolunteerProfile.is_available.is_(True))
        .filter(VolunteerProfile.latitude.is_not(None))
        .filter(VolunteerProfile.longitude.is_not(None))
        .all()
    )
    if not candidates:
        return None

    scored: list[tuple[float, VolunteerProfile]] = []
    for volunteer in candidates:
        distance = haversine_km(latitude, longitude, volunteer.latitude, volunteer.longitude)
        experience_match = animal_type in volunteer.experience_list() or not volunteer.experience_list()
        score = (
            (35 if experience_match else 10)
            + (25 if volunteer.has_vehicle else 5)
            + max(0.0, 40 - distance * 4)
            + (volunteer.rating * 2)
        )
        scored.append((score, volunteer))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def distance_to_volunteer(volunteer: VolunteerProfile, latitude: float, longitude: float) -> float:
    if volunteer.latitude is None or volunteer.longitude is None:
        return 0.0
    return round(haversine_km(latitude, longitude, volunteer.latitude, volunteer.longitude), 2)
