import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import models
from backend.auth.security import get_password_hash
from backend.core.config import settings
from backend.utils.layout_generator import generate_layout
from datetime import date, datetime, timezone


def ensure_published_layout(db: Session, screen) -> None:
    """Ensure `screen` has a real, published seat map.

    Reuses the same layout_generator + TheatreLayout/SeatDefinition
    architecture as the admin Layout Designer (see
    backend/utils/layout_generator.py, backend/models/layout.py) instead of
    inventing a parallel seating representation. Without this, a freshly
    seeded screen only has a `total_seats` count and no actual seats — the
    seat-selection page has nothing to render and booking would accept
    unvalidated seat names.

    Idempotent: does nothing if the screen already has a published layout.
    """
    existing = (
        db.query(models.TheatreLayout)
        .filter(
            models.TheatreLayout.screen_id == screen.id,
            models.TheatreLayout.status == "published",
        )
        .first()
    )
    if existing:
        return

    template = "IMAX" if (screen.screen_type or "").upper() == "IMAX" else "STANDARD"
    layout_data = generate_layout(total_seats=screen.total_seats, template=template)

    layout = models.TheatreLayout(
        theatre_id=screen.theatre_id,
        screen_id=screen.id,
        layout_name="Default Layout",
        layout_type=template,
        total_seats=layout_data.total_seats,
        rows=layout_data.rows,
        cols=layout_data.cols,
        status="published",
        version=1,
        is_published=True,
    )
    db.add(layout)
    db.flush()  # get layout.id

    for seat in layout_data.seats:
        db.add(models.SeatDefinition(
            layout_id=layout.id,
            seat_code=seat.seat_code,
            row_label=seat.row_label,
            seat_number=seat.seat_number,
            seat_type=seat.seat_type,
            category=seat.category,
            position_x=seat.position_x,
            position_y=seat.position_y,
            is_active=seat.is_active,
        ))
    db.flush()
    print(f"  ✓ Published seat layout for '{screen.name}' ({layout_data.total_seats} seats)")


def seed_database():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Seeding Admin User granularly
        if not db.query(models.User).filter(models.User.username == "admin").first():
            print("Seeding Admin User...")
            admin_password = settings.ADMIN_PASSWORD
            if not admin_password:
                if settings.is_production:
                    raise RuntimeError(
                        "[SEED ERROR] ADMIN_PASSWORD environment variable is not set. "
                        "Refusing to seed an admin account with a known default password "
                        "in production. Set ADMIN_PASSWORD in your environment configuration "
                        "and re-run this script."
                    )
                print(
                    "\n[WARNING] ADMIN_PASSWORD is not set.\n"
                    "  Admin will be created with a temporary placeholder password.\n"
                    "  CHANGE THIS IMMEDIATELY after seeding!\n"
                )
                admin_password = "cinema-plus-change-me"

            admin = models.User(
                username="admin",
                email=settings.ADMIN_EMAIL or "admin@cinemaplus.local",
                hashed_password=get_password_hash(admin_password),
                role="admin",
            )
            db.add(admin)
            db.flush()
            print(f"  ✓ Admin user created (email: {admin.email})")

        # Seeding Movies granularly
        movies = db.query(models.Movie).all()
        if not movies:
            print("Seeding Movies...")
            movies = [
                models.Movie(
                    title="Dune: Part Two",
                    genre="Sci-Fi",
                    language="English",
                    format="IMAX 3D",
                    release_date=date(2024, 3, 1),
                    running_days=45,
                    poster_url="https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2JGqqUT1O.jpg",
                    description="Paul Atreides unites with Chani and the Fremen while on a warpath of revenge against the conspirators who destroyed his family.",
                    duration=166,
                    rating=8.8,
                    is_deleted=False,
                ),
                models.Movie(
                    title="Oppenheimer",
                    genre="Biography",
                    language="English",
                    format="IMAX 70mm",
                    release_date=date(2023, 7, 21),
                    running_days=60,
                    poster_url="https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
                    description="The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
                    duration=180,
                    rating=8.6,
                    is_deleted=False,
                ),
            ]
            db.add_all(movies)
            db.flush()

        # Seeding Theatres granularly
        theatre = db.query(models.Theatre).first()
        if not theatre:
            print("Seeding Theatres...")
            theatre = models.Theatre(
                name="Grand Plaza Cinema",
                address="100 Luxury Avenue",
                city="Metropolis",
                state="NY",
                timezone="UTC",
                contact_info="contact@grandplaza.com",
                description="The most premium cinema viewing experience in town featuring leather recliners and gourmet dining.",
                is_active=True,
            )
            db.add(theatre)
            db.flush()

        # Seeding Screens granularly
        screens = db.query(models.Screen).all()
        if not screens and theatre:
            print("Seeding Screens...")
            screen1 = models.Screen(
                theatre_id=theatre.id,
                name="Screen 1 (IMAX)",
                screen_type="IMAX",
                total_seats=220,
                is_active=True,
            )
            screen2 = models.Screen(
                theatre_id=theatre.id,
                name="Screen 2 (Dolby Atmos)",
                screen_type="Dolby Atmos",
                total_seats=220,
                is_active=True,
            )
            db.add_all([screen1, screen2])
            db.flush()
        else:
            screen1 = db.query(models.Screen).filter(models.Screen.name.like("%IMAX%")).first()
            screen2 = db.query(models.Screen).filter(models.Screen.name.like("%Dolby%")).first()

        # Ensure every seeded screen has a published, bookable seat map.
        # Runs regardless of whether screens were just created above or
        # already existed, so re-running this script also backfills layouts
        # for any screen that's missing one.
        print("Verifying seat layouts...")
        for screen in db.query(models.Screen).all():
            ensure_published_layout(db, screen)

        # Seeding Default Seat Pricings granularly
        pricings = db.query(models.SeatPricing).all()
        if not pricings and theatre:
            print("Seeding Default Seat Pricings...")
            s1_id = screen1.id if screen1 else None
            s2_id = screen2.id if screen2 else None
            for s_id in [None, s1_id, s2_id]:
                if s_id is not None or not db.query(models.SeatPricing).filter(
                    models.SeatPricing.theatre_id == theatre.id,
                    models.SeatPricing.screen_id == s_id,
                ).first():
                    db.add_all([
                        models.SeatPricing(theatre_id=theatre.id, screen_id=s_id, seat_category="Normal", base_price=150.0),
                        models.SeatPricing(theatre_id=theatre.id, screen_id=s_id, seat_category="Executive", base_price=220.0),
                        models.SeatPricing(theatre_id=theatre.id, screen_id=s_id, seat_category="Premium", base_price=300.0),
                    ])
            db.flush()

        # Seeding Shows granularly
        shows = db.query(models.Show).all()
        if not shows and movies and screen1 and screen2:
            print("Seeding Shows...")
            show1 = models.Show(
                movie_id=movies[0].id,
                screen_id=screen1.id,
                start_time="13:00",
                end_time="15:46",
                date=date.today(),
                price_multiplier=1.0,
            )
            show2 = models.Show(
                movie_id=movies[1].id,
                screen_id=screen2.id,
                start_time="18:00",
                end_time="21:00",
                date=date.today(),
                price_multiplier=1.0,
            )
            db.add_all([show1, show2])

        db.commit()
        print("Database verification & modular seeding complete!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
