import io
import os

from fastapi import status
from PIL import Image


def _admin_headers(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == status.HTTP_200_OK
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _real_png_bytes(size=(64, 64)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color=(120, 30, 30)).save(buf, format="PNG")
    return buf.getvalue()


def test_movie_poster_upload_file_succeeds_and_persists_to_disk(client):
    """The full flow this feature actually depends on:
    POST /api/movies/upload-poster -> MediaService -> local disk storage
    (uploads/media/original/) -> a poster_url the frontend can attach to a
    Movie record via the normal create/update endpoints."""
    headers = _admin_headers(client)
    png_bytes = _real_png_bytes()

    res = client.post(
        "/api/movies/upload-poster",
        files={"file": ("poster.png", png_bytes, "image/png")},
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK
    poster_url = res.json()["data"]["poster_url"]
    assert poster_url.startswith("/uploads/media/original/")

    # The file was actually written to the persistent uploads directory —
    # not just a URL string with nothing behind it.
    relative_path = poster_url.lstrip("/")
    assert os.path.exists(relative_path), f"expected uploaded file at {relative_path}"

    # And that URL is exactly what the admin movie form attaches to a movie.
    from datetime import date

    movie_payload = {
        "title": "Poster Upload Test Movie",
        "genre": "Drama",
        "language": "English",
        "format": "2D",
        "release_date": str(date.today()),
        "running_days": 30,
        "description": "Poster flow test.",
        "duration": 100,
        "rating": 7.0,
        "status": "Now Showing",
        "poster_url": poster_url,
    }
    res_create = client.post("/api/movies/", json=movie_payload, headers=headers)
    assert res_create.status_code == status.HTTP_201_CREATED
    movie_id = res_create.json()["data"]["id"]
    assert res_create.json()["data"]["poster_url"] == poster_url

    # Customer-facing movie detail page reads the same field back.
    res_detail = client.get(f"/api/movies/{movie_id}")
    assert res_detail.status_code == status.HTTP_200_OK
    assert res_detail.json()["data"]["poster_url"] == poster_url


def test_movie_poster_upload_rejects_invalid_extension(client):
    headers = _admin_headers(client)
    res = client.post(
        "/api/movies/upload-poster",
        files={"file": ("poster.txt", b"not an image", "image/png")},
        headers=headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_movie_poster_upload_rejects_corrupt_image(client):
    headers = _admin_headers(client)
    res = client.post(
        "/api/movies/upload-poster",
        files={"file": ("poster.png", b"\x89PNGnotarealimage" * 100, "image/png")},
        headers=headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_movie_poster_upload_rejects_oversized_file(client):
    headers = _admin_headers(client)
    oversized = b"\x00" * (2 * 1024 * 1024 + 1)  # just over the 2MB limit
    res = client.post(
        "/api/movies/upload-poster",
        files={"file": ("poster.png", oversized, "image/png")},
        headers=headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_movie_poster_upload_requires_admin(client):
    res = client.post(
        "/api/auth/register",
        json={"username": "poster_probe_user", "email": "poster_probe_user@example.com", "password": "testpassword123"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    login = client.post("/api/auth/login", json={"username": "poster_probe_user", "password": "testpassword123"})
    token = login.json()["data"]["access_token"]

    res = client.post(
        "/api/movies/upload-poster",
        files={"file": ("poster.png", _real_png_bytes(), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_standalone_media_library_endpoints_no_longer_exist(client):
    """The standalone Admin Media Library (src/app/admin/media/page.tsx) was
    removed — it could not even list its own uploads and had no real
    consumer. Its backend routes must be gone too, not left dangling."""
    headers = _admin_headers(client)

    res = client.post(
        "/api/admin/media/upload-url",
        json={"image_url": "https://example.com/image.jpg"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

    res = client.post(
        "/api/admin/media/upload",
        files={"file": ("poster.png", _real_png_bytes(), "image/png")},
        headers=headers,
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

    res = client.delete("/api/admin/media/1", headers=headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
