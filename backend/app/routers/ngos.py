from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.report import Report, ReportStatus
from app.models.user import User, UserRole
from app.models.ngo import NGOProfile
from app.schemas.report import ReportOut
from app.schemas.volunteer import NGOProfileOut, NGOProfileUpdate

router = APIRouter(prefix="/api/ngos", tags=["NGOs"])


def _get_own_profile(user: User, db: Session) -> NGOProfile:
    profile = db.query(NGOProfile).filter(NGOProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(404, "NGO profile not found for this account.")
    return profile


@router.get("/me", response_model=NGOProfileOut)
def get_my_profile(user: User = Depends(require_roles(UserRole.NGO)), db: Session = Depends(get_db)):
    return _get_own_profile(user, db)


@router.put("/me", response_model=NGOProfileOut)
def update_my_profile(
    payload: NGOProfileUpdate,
    user: User = Depends(require_roles(UserRole.NGO)),
    db: Session = Depends(get_db),
):
    profile = _get_own_profile(user, db)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/incoming-cases", response_model=list[ReportOut])
def incoming_cases(user: User = Depends(require_roles(UserRole.NGO)), db: Session = Depends(get_db)):
    profile = _get_own_profile(user, db)
    reports = (
        db.query(Report)
        .filter(Report.assigned_ngo_id == profile.id)
        .order_by(Report.priority_score.desc(), Report.created_at.desc())
        .all()
    )
    from app.routers.reports import _attach_volunteer
    return [_attach_volunteer(db, r) for r in reports]


@router.post("/me/claim/{report_id}", response_model=ReportOut)
def claim_case(report_id: str, user: User = Depends(require_roles(UserRole.NGO)), db: Session = Depends(get_db)):
    profile = _get_own_profile(user, db)
    report = db.query(Report).filter((Report.id == report_id) | (Report.display_id == report_id)).first()
    if not report:
        raise HTTPException(404, "Rescue report not found.")

    report.assigned_ngo_id = profile.id
    if report.status in (ReportStatus.ANIMAL_RESCUED,):
        report.status = ReportStatus.HOSPITAL_REACHED
    db.commit()
    db.refresh(report)

    from app.routers.reports import _attach_volunteer
    return _attach_volunteer(db, report)


@router.get("", response_model=list[NGOProfileOut])
def list_ngos(db: Session = Depends(get_db)):
    return db.query(NGOProfile).all()
