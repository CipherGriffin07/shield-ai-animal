from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/api/users", tags=["Users"])


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    city: str | None = None
    avatar_url: str | None = None


class PreferencesUpdate(BaseModel):
    theme_preference: str | None = None
    language_preference: str | None = None


@router.get("/me", response_model=UserPublic)
def get_my_profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserPublic)
def update_my_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/me/preferences", response_model=UserPublic)
def update_preferences(payload: PreferencesUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.theme_preference:
        user.theme_preference = payload.theme_preference
    if payload.language_preference:
        user.language_preference = payload.language_preference
    db.commit()
    db.refresh(user)
    return user
