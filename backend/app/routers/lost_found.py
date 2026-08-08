from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user_optional
from app.models.lost_found import LostFoundMatch, LostFoundPost, LostFoundStatus, LostFoundType
from app.models.user import User
from app.schemas.misc import LostFoundMatchOut, LostFoundPostOut
from app.services.notification_service import notify_in_app
from app.services.similarity_service import compute_image_signature, similarity_score
from app.utils.geo import haversine_km

router = APIRouter(prefix="/api/lost-found", tags=["Lost & Found"])
UPLOAD_DIR = Path(settings.upload_dir)

SIMILARITY_THRESHOLD = 0.80
SEARCH_RADIUS_KM = 25.0


def _out(post: LostFoundPost) -> LostFoundPostOut:
    return LostFoundPostOut(
        id=post.id, post_type=post.post_type, animal_type=post.animal_type, breed=post.breed,
        color_markings=post.color_markings, description=post.description,
        image_url="/" + post.image_path.replace("\\", "/"), last_seen_landmark=post.last_seen_landmark,
        latitude=post.latitude, longitude=post.longitude, contact_phone=post.contact_phone,
        status=post.status, created_at=post.created_at,
    )


@router.post("", response_model=LostFoundPostOut, status_code=201)
async def create_post(
    post_type: LostFoundType = Form(...),
    animal_type: str = Form(...),
    breed: str = Form(""),
    color_markings: str = Form(""),
    description: str = Form(...),
    last_seen_landmark: str = Form(""),
    latitude: float = Form(...),
    longitude: float = Form(...),
    contact_phone: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if not current_user:
        raise HTTPException(401, "Sign in to create a Lost & Found post.")
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Please upload a valid image.")

    suffix = Path(image.filename or "upload.jpg").suffix.lower() or ".jpg"
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / safe_name
    with destination.open("wb") as output:
        output.write(await image.read())

    signature = compute_image_signature(str(destination))

    post = LostFoundPost(
        posted_by_id=current_user.id, post_type=post_type, animal_type=animal_type, breed=breed or None,
        color_markings=color_markings or None, description=description, image_path=f"uploads/{safe_name}",
        image_signature=signature, last_seen_landmark=last_seen_landmark or None,
        latitude=latitude, longitude=longitude, contact_phone=contact_phone,
    )
    db.add(post)
    db.flush()

    # Search the opposite category (lost <-> found) for candidate matches.
    opposite_type = LostFoundType.FOUND if post_type == LostFoundType.LOST else LostFoundType.LOST
    candidates = (
        db.query(LostFoundPost)
        .filter(LostFoundPost.post_type == opposite_type)
        .filter(LostFoundPost.status == LostFoundStatus.OPEN)
        .filter(LostFoundPost.animal_type == animal_type)
        .all()
    )

    best_match = None
    for candidate in candidates:
        distance = haversine_km(latitude, longitude, candidate.latitude, candidate.longitude)
        if distance > SEARCH_RADIUS_KM:
            continue
        score = similarity_score(signature, candidate.image_signature)
        if score >= SIMILARITY_THRESHOLD:
            match = LostFoundMatch(
                source_post_id=post.id, candidate_post_id=candidate.id,
                similarity_score=score, distance_km=round(distance, 2),
            )
            db.add(match)
            if best_match is None or score > best_match[0]:
                best_match = (score, candidate)

    if best_match:
        post.status = LostFoundStatus.MATCHED
        _, matched_candidate = best_match
        matched_candidate.status = LostFoundStatus.MATCHED
        notify_in_app(
            db, post.posted_by_id, "Possible match found",
            f"We found a possible match for your {post_type.value} report - check the Lost & Found page.",
        )
        if matched_candidate.posted_by_id:
            notify_in_app(
                db, matched_candidate.posted_by_id, "Possible match found",
                "Someone posted a report that may match an animal you reported - check the Lost & Found page.",
            )

    db.commit()
    db.refresh(post)
    return _out(post)


@router.get("", response_model=list[LostFoundPostOut])
def list_posts(post_type: LostFoundType | None = None, db: Session = Depends(get_db)):
    query = db.query(LostFoundPost)
    if post_type:
        query = query.filter(LostFoundPost.post_type == post_type)
    posts = query.order_by(LostFoundPost.created_at.desc()).all()
    return [_out(p) for p in posts]


@router.get("/{post_id}/matches", response_model=list[LostFoundMatchOut])
def get_matches(post_id: str, db: Session = Depends(get_db)):
    post = db.get(LostFoundPost, post_id)
    if not post:
        raise HTTPException(404, "Lost & Found post not found.")

    matches = db.query(LostFoundMatch).filter(LostFoundMatch.source_post_id == post_id).all()
    results = []
    for match in matches:
        candidate = db.get(LostFoundPost, match.candidate_post_id)
        if candidate:
            results.append(LostFoundMatchOut(
                candidate_post=_out(candidate),
                similarity_score=match.similarity_score,
                distance_km=match.distance_km,
            ))
    return results
