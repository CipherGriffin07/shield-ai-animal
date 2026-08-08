"""
SHIELD AI - Animal Rescue Platform
Main FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

API docs available at /docs once running.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import (
    admin,
    adoption,
    auth,
    chat,
    hospitals,
    lost_found,
    medical_report,
    ngos,
    reports,
    users,
    volunteers,
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = Path(settings.upload_dir)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered animal rescue coordination platform: reporting, triage, "
                "volunteer/NGO matching, tracking, lost & found, and adoption.",
)

origins = ["*"] if settings.cors_origins == "*" else [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# --- Static frontend + uploaded media ---
STATIC_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- API routers ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(medical_report.router)
app.include_router(volunteers.router)
app.include_router(ngos.router)
app.include_router(hospitals.router)
app.include_router(lost_found.router)
app.include_router(adoption.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


# --- Frontend page routes (serve the static SPA-style pages) ---
FRONTEND_PAGES = [
    "", "login", "signup", "forgot-password", "dashboard", "report", "analysis",
    "tracking", "volunteer", "ngo", "admin", "chatbot", "lost-found", "adoption", "settings",
]


def _serve_page(name: str):
    filename = "index.html" if name == "" else f"{name}.html"
    file_path = STATIC_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    return FileResponse(STATIC_DIR / "index.html")


for _page in FRONTEND_PAGES:
    app.get(f"/{_page}", include_in_schema=False)(lambda name=_page: _serve_page(name))
