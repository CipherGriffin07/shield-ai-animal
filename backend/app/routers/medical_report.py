from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.hospital import Hospital
from app.models.report import Report
from app.models.user import User, UserRole
from app.models.volunteer import VolunteerProfile
from app.services.pdf_service import generate_medical_report_pdf

router = APIRouter(prefix="/api/reports", tags=["Medical Reports"])


@router.get("/{report_id}/medical-report.pdf")
def download_medical_report(
    report_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.NGO, UserRole.VETERINARIAN, UserRole.ADMIN, UserRole.VOLUNTEER)),
):
    report = db.query(Report).filter((Report.id == report_id) | (Report.display_id == report_id)).first()
    if not report:
        raise HTTPException(404, "Rescue report not found.")

    volunteer = db.get(VolunteerProfile, report.assigned_volunteer_id) if report.assigned_volunteer_id else None
    hospital = db.get(Hospital, report.assigned_hospital_id) if report.assigned_hospital_id else None

    output_path = str(Path(tempfile.gettempdir()) / f"{report.display_id}-medical-report.pdf")
    generate_medical_report_pdf(report, hospital, volunteer, report.tracking_events, output_path)

    return FileResponse(
        output_path, media_type="application/pdf",
        filename=f"{report.display_id}-medical-report.pdf",
    )
