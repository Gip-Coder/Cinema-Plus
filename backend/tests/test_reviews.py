import pytest
from fastapi import status
from datetime import date

def test_movie_reviews(client):
    # 1. Login admin to create a movie
    admin_login = {
        "username": "admin",
        "password": "admin123"
    }
    res_login = client.post("/api/auth/login", json=admin_login)
    token = res_login.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}
    
    # Create movie
    movie_payload = {
        "title": "Tenet",
        "genre": "Action",
        "language": "English",
        "format": "2D",
        "release_date": str(date.today()),
        "running_days": 30,
        "description": "Time inversion.",
        "duration": 150,
        "rating": 7.5,
        "status": "Now Showing"
    }
    res_movie = client.post("/api/movies/", json=movie_payload, headers=admin_headers)
    movie_id = res_movie.json()["data"]["id"]
    
    # 2. Register and Login normal user to post review
    user_payload = {
        "username": "reviewuser_test",
        "email": "reviewuser_test@example.com",
        "password": "normalpassword123"
    }
    res_reg = client.post("/api/auth/register", json=user_payload)
    assert res_reg.status_code == status.HTTP_201_CREATED
    
    res_user_login = client.post("/api/auth/login", json={
        "username": "reviewuser_test",
        "password": "normalpassword123"
    })
    user_token = res_user_login.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Post review
    review_payload = {
        "movie_id": movie_id,
        "rating": 8.0,
        "comment": "Mind-bending time travel movie!"
    }
    res_review = client.post("/api/reviews/", json=review_payload, headers=user_headers)
    assert res_review.status_code == status.HTTP_201_CREATED
    review_id = res_review.json()["data"]["id"]
    assert res_review.json()["data"]["rating"] == 8.0
    
    # 3. Get reviews for movie
    res_get_reviews = client.get(f"/api/reviews/movie/{movie_id}")
    assert res_get_reviews.status_code == status.HTTP_200_OK
    assert len(res_get_reviews.json()["data"]) >= 1
    
    # 4. Update review
    update_payload = {
        "movie_id": movie_id,
        "rating": 9.0,
        "comment": "Excellent direction and concept!"
    }
    res_update = client.put(f"/api/reviews/{review_id}", json=update_payload, headers=user_headers)
    assert res_update.status_code == status.HTTP_200_OK
    assert res_update.json()["data"]["rating"] == 9.0
    assert res_update.json()["data"]["comment"] == "Excellent direction and concept!"
    
    # 5. Admin fetches all reviews
    res_all = client.get("/api/reviews/all", headers=admin_headers)
    assert res_all.status_code == status.HTTP_200_OK
    
    # 6. Delete review
    res_del = client.delete(f"/api/reviews/{review_id}", headers=user_headers)
    assert res_del.status_code == status.HTTP_200_OK
