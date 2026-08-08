"""
Cloudinary media storage.

Requires CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and
CLOUDINARY_API_SECRET. Sign up free at https://cloudinary.com

When these are not configured, upload_image() raises
CloudinaryNotConfigured so callers (see app/routers/reports.py) fall
back to local disk storage under /uploads instead of pretending a
cloud upload happened.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import settings


class CloudinaryNotConfigured(RuntimeError):
    pass


def _is_configured() -> bool:
    return bool(settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret)


@lru_cache(maxsize=1)
def _get_client():
    import cloudinary

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    return cloudinary


def upload_image(file_path: str, folder: str = "shield-ai") -> dict:
    if not _is_configured():
        raise CloudinaryNotConfigured("Cloudinary credentials are not configured.")

    import cloudinary.uploader

    _get_client()
    result = cloudinary.uploader.upload(file_path, folder=folder, resource_type="image")
    return {"url": result["secure_url"], "public_id": result["public_id"]}


def delete_image(public_id: str) -> None:
    if not _is_configured():
        raise CloudinaryNotConfigured("Cloudinary credentials are not configured.")

    import cloudinary.uploader

    _get_client()
    cloudinary.uploader.destroy(public_id)
