from backend.models import models
from scripts.seed_db import ensure_published_layout


def test_ensure_published_layout_creates_bookable_seat_map(db):
    theatre = models.Theatre(name="Seed Test Theatre", address="1 Test St", city="Testville")
    db.add(theatre)
    db.flush()

    screen = models.Screen(theatre_id=theatre.id, name="Seed Test Screen", screen_type="IMAX", total_seats=40, is_active=True)
    db.add(screen)
    db.flush()

    # Before: no published layout exists — this is exactly the state a
    # screen created only via total_seats (the old seed_db.py behavior) was
    # left in, which surfaced as "No published seating plan available".
    assert (
        db.query(models.TheatreLayout)
        .filter(models.TheatreLayout.screen_id == screen.id, models.TheatreLayout.status == "published")
        .first()
        is None
    )

    ensure_published_layout(db, screen)
    db.commit()

    layout = (
        db.query(models.TheatreLayout)
        .filter(models.TheatreLayout.screen_id == screen.id, models.TheatreLayout.status == "published")
        .first()
    )
    assert layout is not None
    assert layout.is_published is True
    assert layout.total_seats > 0

    seats = db.query(models.SeatDefinition).filter(models.SeatDefinition.layout_id == layout.id).all()
    assert len(seats) == layout.total_seats
    assert all(s.seat_code for s in seats)
    assert all(s.category in ("Normal", "Executive", "Premium") for s in seats)

    # Idempotent: running it again for the same screen must not create a
    # second published layout or duplicate seats.
    ensure_published_layout(db, screen)
    db.commit()
    layouts = (
        db.query(models.TheatreLayout)
        .filter(models.TheatreLayout.screen_id == screen.id, models.TheatreLayout.status == "published")
        .all()
    )
    assert len(layouts) == 1
