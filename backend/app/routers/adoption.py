from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models.adoption import AdoptionApplication, AdoptionListing, AdoptionStatus, ApplicationStatus
from app.models.animal import Animal
from app.models.ngo import NGOProfile
from app.models.user import User, UserRole
from app.schemas.misc import (
    AdoptionApplicationCreate,
    AdoptionApplicationOut,
    AdoptionListingOut,
)
from app.services.adoption_engine import score_application

router = APIRouter(prefix="/api/adoption", tags=["Adoption"])


def _listing_out(listing: AdoptionListing) -> AdoptionListingOut:
    return AdoptionListingOut(
        id=listing.id, animal_id=listing.animal_id, title=listing.title, story=listing.story,
        temperament_tags=[t.strip() for t in listing.temperament_tags.split(",") if t.strip()],
        status=listing.status, created_at=listing.created_at,
    )


@router.get("/listings", response_model=list[AdoptionListingOut])
def list_listings(db: Session = Depends(get_db)):
    listings = db.query(AdoptionListing).filter(AdoptionListing.status == AdoptionStatus.AVAILABLE).all()
    return [_listing_out(l) for l in listings]


@router.get("/listings/{listing_id}", response_model=AdoptionListingOut)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.get(AdoptionListing, listing_id)
    if not listing:
        raise HTTPException(404, "Adoption listing not found.")
    return _listing_out(listing)


@router.post("/listings/{animal_id}", response_model=AdoptionListingOut, status_code=201)
def create_listing(
    animal_id: str,
    title: str,
    story: str = "",
    temperament_tags: str = "",
    user: User = Depends(require_roles(UserRole.NGO, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    animal = db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(404, "Animal record not found.")

    ngo_profile = db.query(NGOProfile).filter(NGOProfile.user_id == user.id).first()
    listing = AdoptionListing(
        animal_id=animal_id, listed_by_ngo_id=ngo_profile.id if ngo_profile else None,
        title=title, story=story, temperament_tags=temperament_tags,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return _listing_out(listing)


@router.post("/applications", response_model=AdoptionApplicationOut, status_code=201)
def apply(
    payload: AdoptionApplicationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.get(AdoptionListing, payload.listing_id)
    if not listing:
        raise HTTPException(404, "Adoption listing not found.")
    if listing.status != AdoptionStatus.AVAILABLE:
        raise HTTPException(400, "This animal is no longer available for adoption.")

    score = score_application(listing, payload.questionnaire)

    application = AdoptionApplication(
        listing_id=listing.id, applicant_id=user.id,
        questionnaire_json=json.dumps(payload.questionnaire.model_dump()),
        compatibility_score=score,
    )
    db.add(application)
    listing.status = AdoptionStatus.PENDING
    db.commit()
    db.refresh(application)

    return AdoptionApplicationOut(
        id=application.id, listing_id=application.listing_id, applicant_id=application.applicant_id,
        compatibility_score=application.compatibility_score, status=application.status,
        created_at=application.created_at,
    )


@router.get("/applications/{listing_id}", response_model=list[AdoptionApplicationOut])
def list_applications_for_listing(
    listing_id: str,
    user: User = Depends(require_roles(UserRole.NGO, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    applications = (
        db.query(AdoptionApplication)
        .filter(AdoptionApplication.listing_id == listing_id)
        .order_by(AdoptionApplication.compatibility_score.desc())
        .all()
    )
    return [
        AdoptionApplicationOut(
            id=a.id, listing_id=a.listing_id, applicant_id=a.applicant_id,
            compatibility_score=a.compatibility_score, status=a.status, created_at=a.created_at,
        )
        for a in applications
    ]


@router.patch("/applications/{application_id}/decision")
def decide_application(
    application_id: str,
    approve: bool,
    notes: str = "",
    user: User = Depends(require_roles(UserRole.NGO, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    application = db.get(AdoptionApplication, application_id)
    if not application:
        raise HTTPException(404, "Application not found.")

    application.status = ApplicationStatus.APPROVED if approve else ApplicationStatus.REJECTED
    application.reviewer_notes = notes or None

    if approve:
        listing = db.get(AdoptionListing, application.listing_id)
        if listing:
            listing.status = AdoptionStatus.ADOPTED

    db.commit()
    return {"application_id": application_id, "status": application.status.value}
