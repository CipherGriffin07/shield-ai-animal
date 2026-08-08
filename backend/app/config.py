"""
Central configuration for the SHIELD AI backend.

All secrets and environment-specific values are read from environment
variables (typically supplied via a `.env` file in local development,
or the platform's environment settings in production - e.g. Render).

Nothing sensitive is hard-coded. If a required key is missing, the
services that depend on it will raise a clear error at call time
rather than failing silently or fabricating a result.
"""
from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    # --- App ---
    app_name: str = "SHIELD AI Animal Rescue API"
    app_version: str = "2.0.0"
    environment: str = "development"

    # --- Database ---
    database_url: str = f"sqlite:///{BASE_DIR / 'shield.db'}"

    # --- Auth / JWT ---
    jwt_secret_key: str = "CHANGE-THIS-SECRET-IN-PRODUCTION-" + os.urandom(8).hex()
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12          # 12 hours
    refresh_token_expire_minutes: int = 60 * 24 * 7      # 7 days

    # --- File storage ---
    upload_dir: str = str(BASE_DIR / "uploads")
    max_upload_mb: int = 15

    # --- Third-party services (optional until keys are supplied) ---
    gemini_api_key: str | None = None
    gemini_vision_model: str = "gemini-2.0-flash"
    gemini_chat_model: str = "gemini-2.0-flash"

    google_maps_api_key: str | None = None

    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

    # --- Email (for notifications / password reset) ---
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_address: str = "no-reply@shield-ai.app"

    # --- CORS ---
    cors_origins: str = "*"


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
