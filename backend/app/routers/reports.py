from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, get_current_user_optional, require_roles
from app.models.report import Report, ReportStatus, SeverityLevel
from app.models.tracking import TrackingEvent
from app.models.user import User, UserRole
from app.models.volunteer import VolunteerProfile
from app.schemas.report import AssignedVolunteerOut, ReportOut, ReportStatusUpdate, TrackingEventOut
from app.services import rule_based_analysis
from app.services.gemini_service import GeminiNotConfigured, GeminiRequestError, analyse_image_with_gemini
from app.services.matching_engine import distance_to_volunteer, find_best_volunteer
from app.services.notification_service import notify_in_app

router = APIRouter(prefix="/api/reports", tags=["Rescue Reports"])

UPLOAD_DIR = Path(settings.upload_dir)
MAX_UPLOAD_BYTES = settings.max_upload_mb * 1024 * 1024


def _serialize(report: Report) -> ReportOut:
    analysis = json.loads(report.analysis_json)
    volunteer_out = None  # populated by _attach_volunteer, which wraps this
    return ReportOut(
        id=report.id,
        display_id=report.display_id,
        reporter_name=report.reporter_name,
        phone=report.phone,
        animal_type=report.animal_type,
        landmark=report.landmark,
        description=report.description,
        image_url="/" + report.image_path.replace("\\", "/"),
        latitude=report.latitude,
        longitude=report.longitude,
        analysis=analysis,
        priority_score=report.priority_score,
        severity=report.severity,
        assigned_volunteer=volunteer_out,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def _attach_volunteer(db: Session, report: Report) -> ReportOut:
    out = _serialize(report)
    if report.assigned_volunteer_id:
        volunteer = db.get(VolunteerProfile, report.assigned_volunteer_id)
        if volunteer:
            out.assigned_volunteer = AssignedVolunteerOut(
                id=volunteer.id,
                name=volunteer.user.full_name if volunteer.user else "Volunteer",
                phone=volunteer.user.phone if volunteer.user else None,
                distance_km=distance_to_volunteer(volunteer, report.latitude, report.longitude),
                has_vehicle=volunteer.has_vehicle,
            )
    return out


@router.post("", response_model=ReportOut, status_code=201)
async def create_report(
    reporter_name: str = Form(...),
    phone: str = Form(...),
    animal_type: str = Form(""),
    landmark: str = Form(""),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Please upload a valid image file.")

    image_bytes = await image.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f"Image exceeds the {settings.max_upload_mb}MB upload limit.")

    suffix = Path(image.filename or "upload.jpg").suffix.lower() or ".jpg"
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / safe_name
    with destination.open("wb") as output:
        output.write(image_bytes)

    animal = rule_based_analysis.infer_animal(animal_type, description, image.filename or "")

    # Try Gemini Vision first; fall back to the deterministic rule-based
    # engine on any failure so a report is never blocked by an AI outage.
    try:
        analysis = await analyse_image_with_gemini(image_bytes, image.content_type, description)
        animal = analysis.get("animal", animal)
    except (GeminiNotConfigured, GeminiRequestError):
        analysis = rule_based_analysis.analyse_report(animal, description)

    priority = rule_based_analysis.calculate_priority(analysis, description)
    severity = SeverityLevel(analysis["severity"])

    year = datetime.utcnow().year
    count = db.query(Report).count() + 1
    display_id = f"SHIELD-{year}-{count:04d}"

    report = Report(
        display_id=display_id,
        reporter_id=current_user.id if current_user else None,
        reporter_name=reporter_name,
        phone=phone,
        animal_type=animal,
        landmark=landmark,
        description=description,
        image_path=f"uploads/{safe_name}",
        latitude=latitude,
        longitude=longitude,
        analysis_json=json.dumps(analysis),
        priority_score=priority,
        severity=severity,
        status=ReportStatus.AI_ASSESSMENT_COMPLETED,
    )
    db.add(report)
    db.flush()

    volunteer = find_best_volunteer(db, animal, latitude, longitude)
    if volunteer:
        report.assigned_volunteer_id = volunteer.id
        report.status = ReportStatus.VOLUNTEER_ASSIGNED
        notify_in_app(
            db, volunteer.user_id, "New rescue assigned to you",
            f"You've been matched to rescue {display_id} ({animal}) near {landmark or 'the reported location'}.",
            related_report_id=report.id,
        )

    db.add(TrackingEvent(report_id=report.id, status=report.status.value, note="Report submitted and AI-assessed."))
    db.commit()
    db.refresh(report)

    return _attach_volunteer(db, report)


@router.get("", response_model=list[ReportOut])
def list_reports(status_filter: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Report)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    reports = query.order_by(Report.priority_score.desc(), Report.created_at.desc()).all()
    return [_attach_volunteer(db, r) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(
        (Report.id == report_id) | (Report.display_id == report_id)
    ).first()
    if not report:
        raise HTTPException(404, "Rescue report not found.")
    return _attach_volunteer(db, report)


@router.get("/{report_id}/timeline", response_model=list[TrackingEventOut])
def get_timeline(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(
        (Report.id == report_id) | (Report.display_id == report_id)
    ).first()
    if not report:
        raise HTTPException(404, "Rescue report not found.")
    return report.tracking_events


@router.patch("/{report_id}/status", response_model=ReportOut)
def update_status(
    report_id: str,
    payload: ReportStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.VOLUNTEER, UserRole.NGO, UserRole.VETERINARIAN, UserRole.ADMIN)),
):
    report = db.query(Report).filter(
        (Report.id == report_id) | (Report.display_id == report_id)
    ).first()
    if not report:
        raise HTTPException(404, "Rescue report not found.")

    report.status = payload.status
    report.updated_at = datetime.utcnow()
    db.add(TrackingEvent(
        report_id=report.id,
        status=payload.status.value,
        note=payload.note,
        actor_user_id=user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
    ))

    if report.reporter_id:
        notify_in_app(
            db, report.reporter_id, f"Update on rescue {report.display_id}",
            f"Status changed to '{payload.status.value}'.", related_report_id=report.id,
        )

    db.commit()
    db.refresh(report)
    return _attach_volunteer(db, report)
