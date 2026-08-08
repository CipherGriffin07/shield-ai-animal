from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models.report import Report, ReportStatus
from app.models.user import User, UserRole
from app.models.volunteer import VolunteerProfile
from app.schemas.report import ReportOut
from app.schemas.volunteer import VolunteerLocationUpdate, VolunteerProfileOut, VolunteerProfileUpdate
from app.utils.geo import haversine_km

router = APIRouter(prefix="/api/volunteers", tags=["Volunteers"])


def _out(profile: VolunteerProfile) -> VolunteerProfileOut:
    return VolunteerProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        animal_experience=profile.experience_list(),
        has_vehicle=profile.has_vehicle,
        years_experience=profile.years_experience,
        is_available=profile.is_available,
        latitude=profile.latitude,
        longitude=profile.longitude,
        total_rescues_completed=profile.total_rescues_completed,
        rating=profile.rating,
        created_at=profile.created_at,
    )


def _get_own_profile(user: User, db: Session) -> VolunteerProfile:
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(404, "Volunteer profile not found for this account.")
    return profile


@router.get("/me", response_model=VolunteerProfileOut)
def get_my_profile(user: User = Depends(require_roles(UserRole.VOLUNTEER)), db: Session = Depends(get_db)):
    return _out(_get_own_profile(user, db))


@router.put("/me", response_model=VolunteerProfileOut)
def update_my_profile(
    payload: VolunteerProfileUpdate,
    user: User = Depends(require_roles(UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
):
    profile = _get_own_profile(user, db)
    profile.animal_experience = ",".join(payload.animal_experience)
    profile.has_vehicle = payload.has_vehicle
    profile.years_experience = payload.years_experience
    profile.is_available = payload.is_available
    db.commit()
    db.refresh(profile)
    return _out(profile)


@router.put("/me/location", response_model=VolunteerProfileOut)
def update_my_location(
    payload: VolunteerLocationUpdate,
    user: User = Depends(require_roles(UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
):
    profile = _get_own_profile(user, db)
    profile.latitude = payload.latitude
    profile.longitude = payload.longitude
    profile.last_location_update = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _out(profile)


@router.get("/me/nearby-cases", response_model=list[ReportOut])
def nearby_cases(
    radius_km: float = 15.0,
    user: User = Depends(require_roles(UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
):
    profile = _get_own_profile(user, db)
    if profile.latitude is None or profile.longitude is None:
        raise HTTPException(400, "Update your location before viewing nearby cases.")

    open_statuses = [
        ReportStatus.AI_ASSESSMENT_COMPLETED.value,
        ReportStatus.VOLUNTEER_ASSIGNED.value,
        ReportStatus.VOLUNTEER_EN_ROUTE.value,
    ]
    candidates = db.query(Report).filter(Report.status.in_(open_statuses)).all()

    nearby = [
        r for r in candidates
        if haversine_km(profile.latitude, profile.longitude, r.latitude, r.longitude) <= radius_km
    ]
    nearby.sort(key=lambda r: r.priority_score, reverse=True)

    from app.routers.reports import _attach_volunteer  # local import avoids circular import at module load
    return [_attach_volunteer(db, r) for r in nearby]


@router.post("/me/accept/{report_id}", response_model=ReportOut)
def accept_case(
    report_id: str,
    user: User = Depends(require_roles(UserRole.VOLUNTEER)),
    db: Session = Depends(get_db),
):
    profile = _get_own_profile(user, db)
    report = db.query(Report).filter((Report.id == report_id) | (Report.display_id == report_id)).first()
    if not report:
        raise HTTPException(404, "Rescue report not found.")

    report.assigned_volunteer_id = profile.id
    report.status = ReportStatus.VOLUNTEER_ASSIGNED
    db.commit()
    db.refresh(report)

    from app.routers.reports import _attach_volunteer
    return _attach_volunteer(db, report)
