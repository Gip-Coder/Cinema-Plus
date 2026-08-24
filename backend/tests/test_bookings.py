import pytest
from fastapi import status
from datetime import date, time, datetime, timedelta

def test_theatre_screen_show_booking(client):
    # 1. Login as admin
    admin_login = {
        "username": "admin",
        "password": "admin123"
    }
    res_login = client.post("/api/auth/login", json=admin_login)
    assert res_login.status_code == status.HTTP_200_OK
    token = res_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create movie
    movie_payload = {
        "title": "Inception",
        "genre": "Sci-Fi",
        "language": "English",
        "format": "2D",
        "release_date": str(date.today()),
        "running_days": 30,
        "description": "Dream sharing.",
        "duration": 148,
        "rating": 8.8,
        "status": "Now Showing",
        "poster_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba"
    }
    res_movie = client.post("/api/movies/", json=movie_payload, headers=headers)
    assert res_movie.status_code == status.HTTP_201_CREATED
    movie_id = res_movie.json()["data"]["id"]
    
    # 3. Create theatre
    theatre_payload = {
        "name": "PVR Forum",
        "city": "Bangalore",
        "address": "Koramangala"
    }
    res_theatre = client.post("/api/schedule/theatres", json=theatre_payload, headers=headers)
    assert res_theatre.status_code == status.HTTP_200_OK
    theatre_id = res_theatre.json()["data"]["id"]
    
    # 4. Create screen
    screen_payload = {
        "name": "Audi 1",
        "total_seats": 50
    }
    res_screen = client.post(f"/api/schedule/screens?theatre_id={theatre_id}", json=screen_payload, headers=headers)
    assert res_screen.status_code == status.HTTP_200_OK
    screen_id = res_screen.json()["data"]["id"]
    
    # 5. Create show
    show_payload = {
        "movie_id": movie_id,
        "screen_id": screen_id,
        "date": str(date.today()),
        "start_time": "18:00:00",
        "end_time": "20:30:00",
        "price_multiplier": 1.0
    }
    res_show = client.post("/api/schedule/shows", json=show_payload, headers=headers)
    assert res_show.status_code == status.HTTP_200_OK
    show_id = res_show.json()["data"]["id"]
    
    # 6. Generate and save layout for screen
    # Preview
    res_preview = client.post("/api/layouts/preview", json={
        "total_seats": 20,
        "template": "classic",
        "custom_cols": 5
    }, headers=headers)
    assert res_preview.status_code == status.HTTP_200_OK
    preview_seats = res_preview.json()["data"]["seats"]
    
    # Save Layout
    layout_save_payload = {
        "screen_id": screen_id,
        "layout_name": "Audi 1 Standard",
        "total_seats": 20,
        "rows": 4,
        "cols": 5,
        "seats": preview_seats
    }
    res_save = client.post("/api/layouts/save", json=layout_save_payload, headers=headers)
    assert res_save.status_code == status.HTTP_201_CREATED
    layout_id = res_save.json()["data"]["id"]
    
    # Publish layout
    res_publish = client.put(f"/api/layouts/{layout_id}/publish", headers=headers)
    assert res_publish.status_code == status.HTTP_200_OK
    
    # 7. Check seat statuses
    res_seats = client.get(f"/api/bookings/seats/{show_id}")
    assert res_seats.status_code == status.HTTP_200_OK
    
    # 8. Create a booking (as normal user)
    # Register normal user
    user_payload = {
        "username": "normaluser",
        "email": "normaluser@example.com",
        "password": "normalpassword"
    }
    res_reg = client.post("/api/auth/register", json=user_payload)
    assert res_reg.status_code == status.HTTP_201_CREATED
    
    # Login normal user
    res_user_login = client.post("/api/auth/login", json={
        "username": "normaluser",
        "password": "normalpassword"
    })
    user_token = res_user_login.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Let's check seats returned and find standard seat labels (e.g. A1, A2)
    # Since we generated classic template, let's look at a seat label.
    # The layout generated seats. Let's make a booking payload.
    booking_payload = {
        "show_id": show_id,
        "movie_id": movie_id,
        "seats": [
            {"seat_name": "A1", "category": "standard"},
            {"seat_name": "A2", "category": "standard"}
        ],
        "total_amount": 500.0
    }
    res_booking = client.post("/api/bookings/book", json=booking_payload, headers=user_headers)
    assert res_booking.status_code == status.HTTP_201_CREATED
    booking_id = res_booking.json()["data"]["id"]
    
    # 9. Get user bookings
    res_user_bk = client.get("/api/bookings/user/bookings", headers=user_headers)
    assert res_user_bk.status_code == status.HTTP_200_OK
    assert len(res_user_bk.json()["data"]) >= 1
    
    # 10. Check seat statuses after booking (A1 and A2 should be booked)
    res_seats_after = client.get(f"/api/bookings/seats/{show_id}")
    assert res_seats_after.status_code == status.HTTP_200_OK
    statuses = res_seats_after.json()["data"]
    # Verify A1 is booked
    assert "A1" in statuses["booked"]
    assert "A2" in statuses["booked"]
