from datetime import date
from unittest.mock import patch

from fastapi import status
from sqlalchemy.exc import IntegrityError

from backend.services.booking_service import BookingService


def _setup_show(client, headers):
    res_movie = client.post(
        "/api/movies/",
        json={
            "title": "Conflict Test Movie",
            "genre": "Drama",
            "language": "English",
            "format": "2D",
            "release_date": str(date.today()),
            "running_days": 30,
            "description": "Test movie.",
            "duration": 100,
            "rating": 7.0,
            "status": "Now Showing",
        },
        headers=headers,
    )
    assert res_movie.status_code == status.HTTP_201_CREATED
    movie_id = res_movie.json()["data"]["id"]

    res_theatre = client.post(
        "/api/schedule/theatres",
        json={"name": "Conflict Theatre", "city": "Testville", "address": "1 Test St"},
        headers=headers,
    )
    theatre_id = res_theatre.json()["data"]["id"]

    res_screen = client.post(
        f"/api/schedule/screens?theatre_id={theatre_id}",
        json={"name": "Screen X", "total_seats": 50},
        headers=headers,
    )
    screen_id = res_screen.json()["data"]["id"]

    res_show = client.post(
        "/api/schedule/shows",
        json={
            "movie_id": movie_id,
            "screen_id": screen_id,
            "date": str(date.today()),
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "price_multiplier": 1.0,
        },
        headers=headers,
    )
    return movie_id, res_show.json()["data"]["id"]


def test_concurrent_seat_booking_conflict_returns_409_not_500(client, db):
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {admin_login.json()['data']['access_token']}"}
    movie_id, show_id = _setup_show(client, headers)

    client.post(
        "/api/auth/register",
        json={"username": "conflict_user", "email": "conflict_user@example.com", "password": "testpassword123"},
    )
    user_login = client.post("/api/auth/login", json={"username": "conflict_user", "password": "testpassword123"})
    user_headers = {"Authorization": f"Bearer {user_login.json()['data']['access_token']}"}

    booking_payload = {
        "show_id": show_id,
        "movie_id": movie_id,
        "seats": [{"seat_name": "A1", "category": "Normal"}],
        "total_amount": 150.0,
    }

    # First booking succeeds normally.
    res1 = client.post("/api/bookings/book", json=booking_payload, headers=user_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    # A second booking for the exact same seat/show simulates the case where
    # the in-app availability check was bypassed (e.g. a genuine race that
    # slipped past it) and only the DB unique constraint catches it. Force
    # that path directly by bypassing the pre-check, so we're specifically
    # verifying the IntegrityError -> 409 translation, not the app-level
    # check that (correctly) would also reject this earlier.
    with patch(
        "backend.services.booking_service.BookingRepository.get_existing_booked_seats",
        return_value=[],
    ):
        res2 = client.post("/api/bookings/book", json=booking_payload, headers=user_headers)

    assert res2.status_code == status.HTTP_409_CONFLICT, (
        f"expected a clean 409 for a genuine seat conflict, got {res2.status_code}: {res2.text}"
    )
