# SHIELD AI — Animal Rescue Platform

**S**mart **H**elp for **I**njured **E**veryday & **L**iving **D**iversity

This is the production backend for SHIELD AI, built in phases on top of the original
hackathon MVP. This phase covers: full database schema, JWT authentication with
5 roles, rescue report intake with AI triage, volunteer/NGO matching, tracking,
lost & found, adoption, admin analytics, and PDF medical reports.

## What's real vs. what needs your keys

Everything in this codebase is fully working code — nothing is a stub. The one
honest limitation: three features call real third-party APIs, and will use a
real, working fallback until you supply credentials:

| Feature | Needs | Fallback while unconfigured |
|---|---|---|
| Image-based injury triage | `GEMINI_API_KEY` | Deterministic rule-based text analysis (same logic as your original MVP) |
| AI chat assistant | `GEMINI_API_KEY` | Rule-based canned guidance by topic |
| Cloud image storage | `CLOUDINARY_*` | Local disk storage under `/uploads` (works fully, just not CDN-backed) |
| Maps/geocoding/directions | `GOOGLE_MAPS_API_KEY` | Haversine-distance calculations (no turn-by-turn routing) |

Lost & Found similarity matching and the volunteer-matching engine are fully
real and don't need any external key — they run on-device (perceptual image
hashing and a distance/experience scoring model).

## Tech stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (SQLite by default, swap `DATABASE_URL` for Postgres/MySQL)
- **Auth:** JWT (access + refresh + password-reset tokens), bcrypt password hashing, 5 roles (Citizen, Volunteer, NGO, Veterinarian, Admin)
- **AI:** Gemini Vision + Gemini Chat (Google AI Studio)
- **Maps:** Google Maps Geocoding/Directions/Places
- **Media:** Cloudinary (optional) or local disk
- **PDF:** reportlab, generated on demand — no stored PDFs

## Picture
<img width="1908" height="1116" alt="image" src="https://github.com/user-attachments/assets/b19edf03-f84a-4600-9b8a-2f71a98d8229" />
<img width="1915" height="1068" alt="image" src="https://github.com/user-attachments/assets/c353170d-22dc-4035-8cae-7fd9af4d998a" />
<img width="1902" height="1116" alt="image" src="https://github.com/user-attachments/assets/95b1bb58-2a43-4ecf-8d0f-29659b457f7c" />
<img width="1894" height="1120" alt="image" src="https://github.com/user-attachments/assets/f292bfa9-d5cd-4915-a1e2-965d8b3b65ed" />
<img width="1919" height="1128" alt="image" src="https://github.com/user-attachments/assets/603b4991-8aea-4c8b-a0b5-6747433c4ae5" />

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in JWT_SECRET_KEY at minimum
python -m app.seed              # creates a demo admin + hospitals + volunteers
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API docs.

**Demo login after seeding:** `admin@shield-ai.app` / `Admin@1234` (change this immediately in any real deployment).

## Verified working (smoke-tested this session)

- Signup with password-strength validation (422 on weak passwords) ✅
- Login issuing access + refresh JWTs ✅
- Report submission → rule-based AI triage → priority scoring → automatic nearest-volunteer matching ✅
- Status updates → tracking timeline entries ✅
- Role-based access control (403 for wrong role, 401 for no token) ✅
- PDF medical report generation and download ✅
- Admin analytics summary ✅

## Project structure

```
shield/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app assembly
│   │   ├── config.py            # env-driven settings
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── security.py          # password hashing + JWT
│   │   ├── deps.py              # auth dependencies, role guards
│   │   ├── seed.py              # demo data seeding
│   │   ├── models/               # SQLAlchemy ORM models (11 tables)
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── routers/              # API endpoints, grouped by feature
│   │   └── services/              # Gemini, Maps, Cloudinary, matching,
│   │                               priority, adoption, similarity, PDF, notifications
│   ├── static/                    # frontend build output goes here
│   ├── uploads/                   # user-uploaded media
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Next phases

1. **Frontend** — landing page, auth flows, and role dashboards (glassmorphism, forest-green theme) — not yet started, since none of the original upload included frontend files.
2. **Hospitals-nearby endpoint wired to Google Maps Places** (currently hospital directory works from DB; live "nearby vets" search needs `GOOGLE_MAPS_API_KEY`).
3. **Notification triggers** on more events (lost & found matches and rescue assignment already fire in-app notifications; extend to email/SMS once SMTP/SMS provider keys are supplied).
4. **Deployment configs** for Render (backend) and Vercel (frontend).
