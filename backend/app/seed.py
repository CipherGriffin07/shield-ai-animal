"""
Seeds the database with a demo admin account, a few hospitals, and a
few volunteers so the platform is immediately explorable after first
run. Safe to re-run: it checks for existing rows before inserting.

Run with:  python -m app.seed
"""
from __future__ import annotations

from app.database import SessionLocal, init_db
from app.models.hospital import Hospital
from app.models.user import User, UserRole
from app.models.volunteer import VolunteerProfile
from app.security import hash_password

DEMO_ADMIN_EMAIL = "admin@shield-ai.app"
DEMO_ADMIN_PASSWORD = "Admin@1234"  # change immediately after first login


def seed():
    init_db()
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).first():
            admin = User(
                full_name="SHIELD Administrator",
                email=DEMO_ADMIN_EMAIL,
                phone="+91-9000000000",
                hashed_password=hash_password(DEMO_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_verified=True,
            )
            db.add(admin)
            print(f"Created demo admin: {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")

        if db.query(Hospital).count() == 0:
            db.add_all([
                Hospital(
                    name="Kolkata Veterinary Emergency Centre", address="Park Street, Kolkata",
                    phone="+91-9830000001", latitude=22.5535, longitude=88.3520,
                    specializations="Trauma,Surgery,General", is_24x7=True,
                ),
                Hospital(
                    name="Salt Lake Animal Hospital", address="Sector V, Salt Lake, Kolkata",
                    phone="+91-9830000002", latitude=22.5800, longitude=88.4200,
                    specializations="General,Orthopedics", is_24x7=False,
                ),
            ])
            print("Seeded demo hospitals.")

        if db.query(User).filter(User.role == UserRole.VOLUNTEER).count() == 0:
            demo_volunteers = [
                ("Rahul Sen", "rahul.sen@shield-ai.app", 22.5726, 88.3639, "Dog,Cat", True),
                ("Priya Das", "priya.das@shield-ai.app", 22.5800, 88.4200, "Bird,Dog,Cat", True),
                ("Arjun Roy", "arjun.roy@shield-ai.app", 22.6200, 88.4500, "Cow,Other", False),
            ]
            for name, email, lat, lng, animals, has_vehicle in demo_volunteers:
                user = User(
                    full_name=name, email=email, phone="+91-9800000000",
                    hashed_password=hash_password("Volunteer@1234"),
                    role=UserRole.VOLUNTEER, is_verified=True,
                )
                db.add(user)
                db.flush()
                db.add(VolunteerProfile(
                    user_id=user.id, animal_experience=animals, has_vehicle=has_vehicle,
                    years_experience=2, is_available=True, latitude=lat, longitude=lng,
                ))
            print("Seeded demo volunteers (password: Volunteer@1234 for each).")

        db.commit()
        print("Seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
