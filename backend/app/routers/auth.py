from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User, UserRole
from app.models.volunteer import VolunteerProfile
from app.models.ngo import NGOProfile
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UserPublic,
)
from app.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    verify_password_reset_token,
)
from app.services.notification_service import send_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        city=payload.city,
    )
    db.add(user)
    db.flush()  # populate user.id before creating dependent profiles

    if payload.role == UserRole.VOLUNTEER:
        db.add(VolunteerProfile(user_id=user.id))
    elif payload.role == UserRole.NGO:
        db.add(NGOProfile(user_id=user.id, organization_name=payload.full_name))

    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
        role=user.role,
        user_id=user.id,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
        role=user.role,
        user_id=user.id,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise ValueError("Not a refresh token.")
    except (JWTError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.")

    user = db.get(User, decoded["sub"])
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account not found or inactive.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
        role=user.role,
        user_id=user.id,
    )


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # Always return a generic response so we don't leak which emails are registered.
    if user:
        reset_token = create_password_reset_token(user.id)
        reset_link = f"https://shield-ai.app/reset-password?token={reset_token}"
        sent = send_email(
            user.email,
            "Reset your SHIELD AI password",
            f"Hello {user.full_name},\n\nUse this link to reset your password (valid for 30 minutes):\n{reset_link}",
        )
        if not sent:
            # SMTP not configured - the token is returned directly so the flow
            # is still usable in development/testing without an email server.
            return {"message": "Password reset token generated.", "dev_reset_token": reset_token}
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_id = verify_password_reset_token(payload.token)
    if not user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token.")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found.")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password has been reset successfully."}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully."}


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
def logout():
    # Stateless JWTs: logout is handled client-side by discarding the tokens.
    # For server-side revocation, add a token-blocklist table keyed by jti.
    return {"message": "Logged out. Discard the access and refresh tokens client-side."}
