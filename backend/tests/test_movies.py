import pytest
from fastapi import status
from datetime import date
from pydantic import ValidationError

from backend.schemas.movie import MovieCreate, MovieUpdate, MovieResponse
from backend.models import models

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


# ── Regression: MovieResponse.duration must accept NULL (unknown runtime) ──
# Some seeded catalog movies (e.g. unreleased titles with no published
# runtime yet) legitimately have duration=NULL at the DB layer, which has
# been nullable since the very first migration. MovieResponse previously
# inherited MovieBase's `duration: int = Field(..., gt=0)`, which crashed
# serialization for any such movie. MovieCreate/MovieUpdate (the write path)
# must remain strict — only the read/response contract should allow NULL.

def _base_movie_kwargs(**overrides):
    kwargs = dict(
        id=1,
        title="Some Movie",
        genre="Action",
        language="English",
        format="2D",
        release_date=date(2026, 12, 18),
        running_days=90,
        poster_url=None,
        poster_source_type="upload",
        description="",
        duration=None,
        rating=None,
        status="Coming Soon",
        poster_uploaded_at=None,
        is_deleted=False,
        deleted_at=None,
    )
    kwargs.update(overrides)
    return kwargs


def test_movie_response_serializes_with_null_duration():
    movie = models.Movie(**{k: v for k, v in _base_movie_kwargs(duration=None).items() if k != "id"})
    movie.id = 1
    parsed = MovieResponse.model_validate(movie)
    assert parsed.duration is None


def test_movie_response_serializes_with_valid_duration():
    movie = models.Movie(**{k: v for k, v in _base_movie_kwargs(duration=166, status="Now Showing").items() if k != "id"})
    movie.id = 2
    parsed = MovieResponse.model_validate(movie)
    assert parsed.duration == 166


def test_movie_create_still_rejects_missing_duration():
    payload = dict(
        title="X", genre="Action", language="English", format="2D",
        release_date=date(2026, 12, 18), running_days=90,
        description="", rating=None, status="Coming Soon",
    )
    with pytest.raises(ValidationError):
        MovieCreate(**payload)  # duration omitted entirely


def test_movie_create_still_rejects_invalid_duration():
    payload = dict(
        title="X", genre="Action", language="English", format="2D",
        release_date=date(2026, 12, 18), running_days=90,
        description="", duration=0, rating=None, status="Coming Soon",
    )
    with pytest.raises(ValidationError):
        MovieCreate(**payload)  # duration must be > 0


def test_movie_update_still_rejects_invalid_duration():
    with pytest.raises(ValidationError):
        MovieUpdate(duration=-5)  # explicit invalid value still rejected

    # Omitting duration entirely on an update remains valid (partial update).
    assert MovieUpdate(title="Renamed").duration is None


def test_get_movies_returns_200_with_unknown_duration_movie(client, db):
    """End-to-end: a movie with duration=NULL must not break GET /api/movies/."""
    known = models.Movie(**{k: v for k, v in _base_movie_kwargs(
        title="Known Runtime Movie", duration=142, status="Now Showing",
        release_date=date(2024, 1, 1),
    ).items() if k != "id"})
    unknown = models.Movie(**{k: v for k, v in _base_movie_kwargs(
        title="Unknown Runtime Movie", duration=None, status="Coming Soon",
        release_date=date(2027, 1, 1),
    ).items() if k != "id"})
    db.add_all([known, unknown])
    db.commit()
    db.refresh(known)
    db.refresh(unknown)

    # movie_routes caches GET /api/movies/ per skip/limit (process-global
    # InMemoryCache) — invalidate so this test doesn't see a stale list from
    # an earlier test in the same session (see conftest's rate-limiter reset
    # for the same class of issue).
    from backend.utils.cache import cache
    cache.invalidate("movie:*")

    res_list = client.get("/api/movies/")
    assert res_list.status_code == status.HTTP_200_OK
    titles = {m["title"]: m["duration"] for m in res_list.json()["data"]}
    assert titles["Known Runtime Movie"] == 142
    assert titles["Unknown Runtime Movie"] is None

    res_detail = client.get(f"/api/movies/{unknown.id}")
    assert res_detail.status_code == status.HTTP_200_OK
    assert res_detail.json()["data"]["duration"] is None

    res_detail_known = client.get(f"/api/movies/{known.id}")
    assert res_detail_known.status_code == status.HTTP_200_OK
    assert res_detail_known.json()["data"]["duration"] == 142
