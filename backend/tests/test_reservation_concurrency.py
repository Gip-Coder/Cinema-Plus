import threading
from unittest.mock import patch
from datetime import date, datetime, timedelta, timezone

from fastapi import status

from backend.database import SessionLocal as TestingSessionLocal
from backend.services.reservation_service import ReservationService
from backend.services.seat_state_service import SeatStateService
from backend.exceptions.reservation_exceptions import SeatsAlreadyReservedException
from backend.models.reservation import ReservationGroup, SeatReservation


def _create_movie_theatre_screen_show(client, headers, title):
    movie_payload = {
        "title": title,
        "genre": "Drama",
        "language": "English",
        "format": "2D",
        "release_date": str(date.today()),
        "running_days": 30,
        "description": "Test movie.",
        "duration": 120,
        "rating": 7.5,
        "status": "Now Showing",
    }
    res_movie = client.post("/api/movies/", json=movie_payload, headers=headers)
    assert res_movie.status_code == status.HTTP_201_CREATED
    movie_id = res_movie.json()["data"]["id"]

    res_theatre = client.post(
        "/api/schedule/theatres",
        json={"name": f"Theatre for {title}", "city": "Testville", "address": "1 Test St"},
        headers=headers,
    )
    assert res_theatre.status_code == status.HTTP_200_OK
    theatre_id = res_theatre.json()["data"]["id"]

    res_screen = client.post(
        f"/api/schedule/screens?theatre_id={theatre_id}",
        json={"name": "Screen A", "total_seats": 50},
        headers=headers,
    )
    assert res_screen.status_code == status.HTTP_200_OK
    screen_id = res_screen.json()["data"]["id"]

    res_show = client.post(
        "/api/schedule/shows",
        json={
            "movie_id": movie_id,
            "screen_id": screen_id,
            "date": str(date.today()),
            "start_time": "18:00:00",
            "end_time": "20:00:00",
            "price_multiplier": 1.0,
        },
        headers=headers,
    )
    assert res_show.status_code == status.HTTP_200_OK
    return res_show.json()["data"]["id"]


def _register_and_get_user_id(client, db, username):
    res = client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "testpassword123"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    return res.json()["data"]["id"]


def test_concurrent_reservation_exactly_one_succeeds(client, db):
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

    show_id = _create_movie_theatre_screen_show(client, headers, "Race Condition Movie")
    seat_name = "A1"

    user1_id = _register_and_get_user_id(client, db, "race_user_one")
    user2_id = _register_and_get_user_id(client, db, "race_user_two")

    # Force both threads past the app-level availability check before either
    # commits its insert, so the outcome is decided purely by the DB-level
    # unique constraint on the active-reservation lock key — this is the
    # exact race scripts/verify_production.py claimed (without proof) was
    # already handled.
    barrier = threading.Barrier(2)
    original_check = SeatStateService.check_availability

    def synced_check(self, show_id_, seat_names_):
        available = original_check(self, show_id_, seat_names_)
        barrier.wait(timeout=5)
        return available

    outcomes = []
    outcomes_lock = threading.Lock()

    def worker(user_id):
        session = TestingSessionLocal()
        service = ReservationService(session)
        try:
            group = service.create_reservation_group(show_id, [seat_name], user_id)
            with outcomes_lock:
                outcomes.append(("success", group.id))
        except SeatsAlreadyReservedException:
            with outcomes_lock:
                outcomes.append(("conflict", None))
        finally:
            session.close()

    with patch.object(SeatStateService, "check_availability", synced_check):
        t1 = threading.Thread(target=worker, args=(user1_id,))
        t2 = threading.Thread(target=worker, args=(user2_id,))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

    successes = [o for o in outcomes if o[0] == "success"]
    conflicts = [o for o in outcomes if o[0] == "conflict"]

    assert len(outcomes) == 2, "both threads must finish (no hang/deadlock)"
    assert len(successes) == 1, f"expected exactly 1 success, got outcomes={outcomes}"
    assert len(conflicts) == 1, f"expected exactly 1 conflict (409-equivalent), got outcomes={outcomes}"

    # DB stays consistent: only one active hold exists for this seat.
    active_holds = (
        db.query(SeatReservation)
        .filter(SeatReservation.show_id == show_id, SeatReservation.seat_id == seat_name, SeatReservation.status == "active")
        .all()
    )
    assert len(active_holds) == 1


def test_expired_reservation_does_not_permanently_block_seat(client, db):
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}

    show_id = _create_movie_theatre_screen_show(client, headers, "Expiry Release Movie")
    seat_name = "B5"
    user_id = _register_and_get_user_id(client, db, "expiry_test_user")

    service = ReservationService(db)
    first_group = service.create_reservation_group(show_id, [seat_name], user_id)
    first_group_id = first_group.id

    # Simulate the hold going stale (RESERVATION_TIMEOUT_MINUTES elapsed)
    # without anyone having actively cancelled it.
    stale_group = db.query(ReservationGroup).filter(ReservationGroup.id == first_group_id).first()
    stale_group.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db.commit()

    # A second user should now be able to reserve the same seat — the
    # generated/partial-unique lock key frees up once cleanup_expired_reservations()
    # (called at the top of create_reservation_group) flips the stale row's
    # status away from "active".
    second_user_id = _register_and_get_user_id(client, db, "expiry_test_user_two")
    second_group = service.create_reservation_group(show_id, [seat_name], second_user_id)
    assert second_group.id != first_group_id

    # Historical row is preserved (not deleted), just marked expired.
    db.refresh(stale_group)
    assert stale_group.status == "expired"
    original_seat_row = (
        db.query(SeatReservation)
        .filter(SeatReservation.reservation_group_id == first_group_id, SeatReservation.seat_id == seat_name)
        .first()
    )
    assert original_seat_row is not None
    assert original_seat_row.status == "expired"

    new_seat_row = (
        db.query(SeatReservation)
        .filter(SeatReservation.reservation_group_id == second_group.id, SeatReservation.seat_id == seat_name)
        .first()
    )
    assert new_seat_row is not None
    assert new_seat_row.status == "active"
