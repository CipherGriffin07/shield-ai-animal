from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.ngo import NGOProfile
from app.models.report import Report, ReportStatus, SeverityLevel
from app.models.user import User, UserRole
from app.models.volunteer import VolunteerProfile
from app.schemas.auth import UserPublic
from app.schemas.misc import DashboardStats, HeatmapPoint, TimeseriesPoint

router = APIRouter(prefix="/api/admin", tags=["Admin"])
_admin_only = require_roles(UserRole.ADMIN)


@router.get("/users", response_model=list[UserPublic])
def list_users(role: UserRole | None = None, db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found.")
    user.is_active = False
    db.commit()
    return {"message": f"{user.full_name} has been deactivated."}


@router.patch("/users/{user_id}/reactivate")
def reactivate_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found.")
    user.is_active = True
    db.commit()
    return {"message": f"{user.full_name} has been reactivated."}


@router.patch("/ngos/{ngo_id}/verify")
def verify_ngo(ngo_id: str, db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    ngo = db.get(NGOProfile, ngo_id)
    if not ngo:
        raise HTTPException(404, "NGO not found.")
    ngo.is_verified = True
    db.commit()
    return {"message": f"{ngo.organization_name} has been verified."}


@router.get("/analytics/summary", response_model=DashboardStats)
def analytics_summary(db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    total = db.query(Report).count()
    critical = db.query(Report).filter(Report.severity == SeverityLevel.CRITICAL).count()
    completed = db.query(Report).filter(Report.status == ReportStatus.CASE_CLOSED).count()
    active = total - completed
    volunteers = db.query(VolunteerProfile).count()
    ngos = db.query(NGOProfile).count()

    # Average time from report creation to "Volunteer Assigned" first event, in minutes.
    from app.models.tracking import TrackingEvent
    assigned_events = (
        db.query(TrackingEvent, Report.created_at)
        .join(Report, Report.id == TrackingEvent.report_id)
        .filter(TrackingEvent.status == ReportStatus.VOLUNTEER_ASSIGNED.value)
        .all()
    )
    if assigned_events:
        deltas = [(event.created_at - created_at).total_seconds() / 60 for event, created_at in assigned_events]
        avg_response = round(sum(deltas) / len(deltas), 1)
    else:
        avg_response = None

    return DashboardStats(
        total_reports=total, critical_reports=critical, active_rescues=active,
        completed_rescues=completed, total_volunteers=volunteers, total_ngos=ngos,
        average_response_minutes=avg_response,
    )


@router.get("/analytics/timeseries", response_model=list[TimeseriesPoint])
def analytics_timeseries(days: int = 30, db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(func.date(Report.created_at).label("day"), func.count(Report.id).label("count"))
        .filter(Report.created_at >= since)
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [TimeseriesPoint(period=str(row.day), count=row.count) for row in rows]


@router.get("/analytics/heatmap", response_model=list[HeatmapPoint])
def analytics_heatmap(db: Session = Depends(get_db), _: User = Depends(_admin_only)):
    reports = db.query(Report.latitude, Report.longitude, Report.priority_score).all()
    return [
        HeatmapPoint(latitude=r.latitude, longitude=r.longitude, weight=max(1, r.priority_score // 20))
        for r in reports
    ]
