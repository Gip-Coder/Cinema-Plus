import pytest
from fastapi import status
from datetime import date

def test_movie_lifecycle(client):
    # 1. List movies (initially empty or seeded)
    res_list = client.get("/api/movies/")
    assert res_list.status_code == status.HTTP_200_OK
    assert res_list.json()["success"] is True
    
    # 2. Login as admin
    admin_login = {
        "username": "admin",
        "password": "admin123"
    }
    res_login = client.post("/api/auth/login", json=admin_login)
    assert res_login.status_code == status.HTTP_200_OK
    token = res_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create a movie (as admin)
    movie_payload = {
        "title": "Interstellar",
        "genre": "Sci-Fi",
        "language": "English",
        "format": "IMAX",
        "release_date": str(date.today()),
        "running_days": 30,
        "description": "A journey through space and time.",
        "duration": 169,
        "rating": 8.6,
        "status": "Now Showing",
        "poster_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba"
    }
    res_create = client.post("/api/movies/", json=movie_payload, headers=headers)
    assert res_create.status_code == status.HTTP_201_CREATED
    movie_id = res_create.json()["data"]["id"]
    assert res_create.json()["data"]["title"] == "Interstellar"
    
    # 4. Try creating movie as normal user (unauthorized check)
    # First register/login normal user
    client.post("/api/auth/register", json={
        "username": "normaluser",
        "email": "normal@example.com",
        "password": "normalpassword"
    })
    res_user_login = client.post("/api/auth/login", json={
        "username": "normaluser",
        "password": "normalpassword"
    })
    normal_token = res_user_login.json()["data"]["access_token"]
    normal_headers = {"Authorization": f"Bearer {normal_token}"}
    
    res_unauth_create = client.post("/api/movies/", json=movie_payload, headers=normal_headers)
    assert res_unauth_create.status_code == status.HTTP_403_FORBIDDEN or res_unauth_create.status_code == status.HTTP_401_UNAUTHORIZED
    
    # 5. Get movie details
    res_detail = client.get(f"/api/movies/{movie_id}")
    assert res_detail.status_code == status.HTTP_200_OK
    assert res_detail.json()["data"]["title"] == "Interstellar"
    
    # 6. Search movie
    res_search = client.get(f"/api/movies/search?q=Interstellar")
    assert res_search.status_code == status.HTTP_200_OK
    assert len(res_search.json()["data"]) >= 1
    
    # 7. Update movie (as admin)
    update_payload = {
        "title": "Interstellar Updated",
        "rating": 9.0
    }
    res_update = client.put(f"/api/movies/{movie_id}", json=update_payload, headers=headers)
    assert res_update.status_code == status.HTTP_200_OK
    assert res_update.json()["data"]["title"] == "Interstellar Updated"
    assert res_update.json()["data"]["rating"] == 9.0
    
    # 8. Delete movie (as admin)
    res_delete = client.delete(f"/api/movies/{movie_id}", headers=headers)
    assert res_delete.status_code == status.HTTP_204_NO_CONTENT
    
    # Get details of deleted movie
    res_detail_del = client.get(f"/api/movies/{movie_id}")
    assert res_detail_del.status_code == status.HTTP_404_NOT_FOUND or res_detail_del.json()["data"] is None or res_detail_del.json()["data"]["is_deleted"] is True
