from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.hospital import Hospital
from app.models.user import User, UserRole
from app.utils.geo import haversine_km

router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])


class HospitalIn(BaseModel):
    name: str
    address: str
    phone: str
    latitude: float
    longitude: float
    specializations: list[str] = []
    is_24x7: bool = False


class HospitalOut(BaseModel):
    id: str
    name: str
    address: str
    phone: str
    latitude: float
    longitude: float
    specializations: list[str]
    is_24x7: bool
    distance_km: float | None = None

    model_config = {"from_attributes": True}


def _out(hospital: Hospital, distance_km: float | None = None) -> HospitalOut:
    return HospitalOut(
        id=hospital.id, name=hospital.name, address=hospital.address, phone=hospital.phone,
        latitude=hospital.latitude, longitude=hospital.longitude,
        specializations=[s.strip() for s in hospital.specializations.split(",") if s.strip()],
        is_24x7=hospital.is_24x7, distance_km=distance_km,
    )


@router.get("", response_model=list[HospitalOut])
def list_hospitals(
    latitude: float | None = None,
    longitude: float | None = None,
    db: Session = Depends(get_db),
):
    hospitals = db.query(Hospital).all()
    if latitude is not None and longitude is not None:
        scored = [(haversine_km(latitude, longitude, h.latitude, h.longitude), h) for h in hospitals]
        scored.sort(key=lambda item: item[0])
        return [_out(h, round(dist, 2)) for dist, h in scored]
    return [_out(h) for h in hospitals]


@router.post("", response_model=HospitalOut, status_code=201)
def create_hospital(
    payload: HospitalIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    hospital = Hospital(
        name=payload.name, address=payload.address, phone=payload.phone,
        latitude=payload.latitude, longitude=payload.longitude,
        specializations=",".join(payload.specializations), is_24x7=payload.is_24x7,
    )
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return _out(hospital)


@router.delete("/{hospital_id}")
def delete_hospital(
    hospital_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    hospital = db.get(Hospital, hospital_id)
    if not hospital:
        raise HTTPException(404, "Hospital not found.")
    db.delete(hospital)
    db.commit()
    return {"message": "Hospital removed."}
