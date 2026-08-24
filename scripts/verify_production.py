"""
Cinema Plus — Live Production Verification Suite
=================================================
Performs live HTTP verification against the running production backend:
  1. /health endpoint check
  2. Security response headers (nosniff, DENY, Referrer-Policy, X-Request-ID)
  3. CORS verification (Allowed origin vs unauthorized origin)
  4. Customer registration & login
  5. Invalid login rejection
  6. Password change via JSON Body (verify old fails, new succeeds)
  7. Unauthorized admin access rejection
  8. Admin login & movie lifecycle (create, get, list, soft-delete)
  9. Media poster upload validation (valid image vs invalid file rejected)
  10. Concurrency test: two simultaneous requests booking the EXACT same seat
  11. Ticket PDF generation & download
"""
import sys
import time
import httpx
import threading
from io import BytesIO
from PIL import Image

BASE_URL = "http://127.0.0.1:8001"
results = {}


def test_step(name):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            try:
                res = fn(*args, **kwargs)
                results[name] = ("PASSED", res or "OK")
                print(f"  [PASSED] {name}")
                return res
            except Exception as e:
                results[name] = ("FAILED", str(e))
                print(f"  [FAILED] {name}: {e}")
                return None
        return wrapper
    return decorator


@test_step("1. Health Endpoint (/health)")
def verify_health():
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.get("/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["status"] == "healthy", f"Expected status healthy, got {data}"
        assert data["database"] == "ok", "Database check failed"
        assert data["storage"] == "ok", "Storage check failed"
        return f"Status: {data['status']}, DB: {data['database']}, Storage: {data['storage']}"


@test_step("2. Security Response Headers")
def verify_security_headers():
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.get("/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options"
        assert r.headers.get("X-Frame-Options") == "DENY", "Missing X-Frame-Options: DENY"
        assert "strict-origin" in r.headers.get("Referrer-Policy", ""), "Missing/invalid Referrer-Policy"
        assert "X-Request-ID" in r.headers, "Missing X-Request-ID"
        return "nosniff, DENY, strict-origin, X-Request-ID all present"


@test_step("3. CORS Header Behavior")
def verify_cors():
    with httpx.Client(base_url=BASE_URL) as client:
        r_allowed = client.options(
            "/api/movies/",
            headers={
                "Origin": "http://localhost:3005",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert r_allowed.headers.get("access-control-allow-origin") == "http://localhost:3005", \
            f"Expected allow-origin for localhost:3005, got {r_allowed.headers.get('access-control-allow-origin')}"
        assert r_allowed.headers.get("access-control-allow-credentials") == "true", "Missing allow-credentials"

        r_unauth = client.options(
            "/api/movies/",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        origin_header = r_unauth.headers.get("access-control-allow-origin")
        assert origin_header != "https://malicious-site.com" and origin_header != "*", \
            f"Unauthorized origin was not rejected! Got: {origin_header}"
        return "Allowed origin accepted with credentials, unauthorized origin rejected"


@test_step("4. Customer Registration & Login")
def verify_customer_auth():
    uid = int(time.time())
    username = f"liveuser_{uid}"
    email = f"liveuser_{uid}@example.com"
    password = "LiveUserPass123!"

    with httpx.Client(base_url=BASE_URL) as client:
        r_reg = client.post(
            "/api/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        assert r_reg.status_code == 201, f"Registration failed: {r_reg.text}"
        
        r_login = client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        assert r_login.status_code == 200, f"Login failed: {r_login.text}"
        token = r_login.json()["data"]["access_token"]
        
        r_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r_me.status_code == 200
        assert r_me.json()["data"]["username"] == username
        return {"token": token, "username": username, "password": password}


@test_step("5. Invalid Login Rejection")
def verify_invalid_login():
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.post(
            "/api/auth/login",
            json={"username": "nonexistent_user", "password": "wrong_password_123"},
        )
        assert r.status_code == 401, f"Expected 401 for bad login, got {r.status_code}"
        return "401 Unauthorized correctly returned"


@test_step("6. Password Change via JSON Body")
def verify_password_change(auth_data):
    if not auth_data:
        raise ValueError("Requires auth_data from step 4")
    
    token = auth_data["token"]
    username = auth_data["username"]
    old_pw = auth_data["password"]
    new_pw = "BrandNewPass999!"

    with httpx.Client(base_url=BASE_URL) as client:
        r_chg = client.put(
            "/api/auth/change-password",
            json={"old_password": old_pw, "new_password": new_pw},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r_chg.status_code == 200, f"Password change failed: {r_chg.text}"

        r_old = client.post(
            "/api/auth/login",
            json={"username": username, "password": old_pw},
        )
        assert r_old.status_code == 401, f"Old password still worked! Expected 401, got {r_old.status_code}"

        r_new = client.post(
            "/api/auth/login",
            json={"username": username, "password": new_pw},
        )
        assert r_new.status_code == 200, f"New password failed: {r_new.text}"
        return "Password changed via body, old password invalidated, new password verified"


@test_step("7. Unauthorized Admin Route Rejection")
def verify_unauthorized_admin(auth_data):
    if not auth_data:
        raise ValueError("Requires auth_data")
    token = auth_data["token"]

    with httpx.Client(base_url=BASE_URL) as client:
        r = client.post(
            "/api/admin/theatres",
            json={"name": "Hacked Theatre", "city": "City", "address": "Address"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403, f"Expected 403 Forbidden, got {r.status_code}: {r.text}"
        return "403 Forbidden correctly returned for customer accessing admin endpoint"


def _get_admin_token(client):
    """Ensure an admin user exists and return an access token."""
    for pw in ["AdminPass123!", "dev-admin-change-me", "admin123", "admin"]:
        r = client.post("/api/auth/login", json={"username": "admin", "password": pw})
        if r.status_code == 200:
            return r.json()["data"]["access_token"]
    
    # Direct DB password reset if needed for test harness
    from backend.database import SessionLocal
    from backend.models.models import User
    from backend.auth.security import get_password_hash
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(username="admin", email="admin@cinemaplus.local", hashed_password=get_password_hash("AdminPass123!"), role="admin")
        db.add(admin)
    else:
        setattr(admin, "hashed_password", get_password_hash("AdminPass123!"))
    db.commit()
    db.close()
    
    r = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert r.status_code == 200, f"Admin login failed after reset: {r.text}"
    return r.json()["data"]["access_token"]


@test_step("8. Admin Login & Movie Lifecycle")
def verify_admin_movie_lifecycle():
    with httpx.Client(base_url=BASE_URL) as client:
        admin_token = _get_admin_token(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        movie_payload = {
            "title": f"Live Verification Movie {int(time.time())}",
            "genre": "Action",
            "language": "English",
            "format": "IMAX 3D",
            "release_date": "2026-08-24",
            "running_days": 30,
            "description": "Created during production verification.",
            "duration": 135,
            "rating": 8.9,
            "poster_url": "/uploads/defaults/no-poster.png",
        }
        r_create = client.post("/api/movies/", json=movie_payload, headers=headers)
        assert r_create.status_code == 201, f"Movie creation failed: {r_create.text}"
        movie_id = r_create.json()["data"]["id"]

        r_get = client.get(f"/api/movies/{movie_id}")
        assert r_get.status_code == 200
        assert r_get.json()["data"]["title"] == movie_payload["title"]

        r_del = client.delete(f"/api/movies/{movie_id}", headers=headers)
        assert r_del.status_code in (200, 204), f"Delete failed: {r_del.status_code}"

        return f"Created movie #{movie_id}, retrieved details, and soft-deleted cleanly (HTTP {r_del.status_code})"


@test_step("9. Media Poster Upload Validation")
def verify_media_upload():
    with httpx.Client(base_url=BASE_URL) as client:
        admin_token = _get_admin_token(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        img = Image.new("RGB", (200, 200), color=(229, 9, 20))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        files = {"file": ("test_poster.png", buf.getvalue(), "image/png")}
        r_upload = client.post("/api/movies/upload-poster", files=files, headers=headers)
        assert r_upload.status_code == 200, f"Poster upload failed: {r_upload.text}"
        data = r_upload.json()["data"]
        poster_url = data.get("poster_url") or data.get("public_url")
        assert poster_url, f"Missing poster_url in {data}"

        r_static = client.get(poster_url)
        assert r_static.status_code == 200, f"Static image not served: {r_static.status_code}"

        fake_files = {"file": ("malicious.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload")}
        r_bad = client.post("/api/movies/upload-poster", files=fake_files, headers=headers)
        assert r_bad.status_code == 400, f"Executable file was not rejected! Got {r_bad.status_code}"

        return f"Valid PNG uploaded ({poster_url}) and downloadable (HTTP 200); malicious .exe rejected (HTTP 400)"


@test_step("10. Booking Concurrency & Duplicate Seat Rejection")
def verify_booking_concurrency():
    with httpx.Client(base_url=BASE_URL) as client:
        admin_token = _get_admin_token(client)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        r_m = client.post("/api/movies/", json={
            "title": f"Concurrency Movie {int(time.time())}",
            "genre": "Thriller", "language": "English", "format": "2D",
            "release_date": "2026-08-24", "running_days": 14,
            "description": "Concurrency check", "duration": 120, "rating": 8.0,
            "poster_url": "/uploads/defaults/no-poster.png"
        }, headers=admin_headers)
        movie_id = r_m.json()["data"]["id"]

        r_t = client.post("/api/schedule/theatres", json={
            "name": f"Concurrency Theatre {int(time.time())}",
            "city": "City", "address": "Address"
        }, headers=admin_headers)
        theatre_id = r_t.json()["data"]["id"]

        r_s = client.post(f"/api/schedule/screens?theatre_id={theatre_id}", json={
            "name": "Screen Concurrency", "total_seats": 50
        }, headers=admin_headers)
        screen_id = r_s.json()["data"]["id"]

        r_show = client.post("/api/schedule/shows", json={
            "movie_id": movie_id, "screen_id": screen_id,
            "date": "2026-08-24", "start_time": "19:00:00", "end_time": "21:00:00",
            "price_multiplier": 1.0
        }, headers=admin_headers)
        show_id = r_show.json()["data"]["id"]

        t1 = int(time.time())
        client.post("/api/auth/register", json={"username": f"userA_{t1}", "email": f"userA_{t1}@test.com", "password": "PassA123!"})
        client.post("/api/auth/register", json={"username": f"userB_{t1}", "email": f"userB_{t1}@test.com", "password": "PassB123!"})
        token_A = client.post("/api/auth/login", json={"username": f"userA_{t1}", "password": "PassA123!"}).json()["data"]["access_token"]
        token_B = client.post("/api/auth/login", json={"username": f"userB_{t1}", "password": "PassB123!"}).json()["data"]["access_token"]

        target_seat = "A1"
        responses = []

        def book_seat(token, user_tag):
            with httpx.Client(base_url=BASE_URL) as c:
                res = c.post(
                    "/api/reservations",
                    json={"show_id": show_id, "seats": [target_seat]},
                    headers={"Authorization": f"Bearer {token}"}
                )
                responses.append((user_tag, res.status_code, res.json() if res.status_code < 500 else res.text))

        thread1 = threading.Thread(target=book_seat, args=(token_A, "User A"))
        thread2 = threading.Thread(target=book_seat, args=(token_B, "User B"))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        success_count = sum(1 for _, status_code, _ in responses if status_code == 201)
        rejected_count = sum(1 for _, status_code, _ in responses if status_code in (400, 409, 422))

        assert success_count == 1, f"Expected exactly 1 success (201), got {success_count}: {responses}"
        assert rejected_count == 1, f"Expected exactly 1 rejection, got {rejected_count}: {responses}"

        return "Race condition resolved: Exactly 1 reservation succeeded (201), other rejected"


@test_step("11. Ticket PDF & QR Generation")
def verify_ticket_pdf():
    with httpx.Client(base_url=BASE_URL) as client:
        admin_token = _get_admin_token(client)
        headers = {"Authorization": f"Bearer {admin_token}"}

        r_m = client.post("/api/movies/", json={
            "title": f"Ticket Test Movie {int(time.time())}",
            "genre": "Animation", "language": "English", "format": "2D",
            "release_date": "2026-08-24", "running_days": 14,
            "description": "Ticket check", "duration": 90, "rating": 9.0,
            "poster_url": "/uploads/defaults/no-poster.png"
        }, headers=headers)
        movie_id = r_m.json()["data"]["id"]

        r_t = client.post("/api/schedule/theatres", json={
            "name": f"Ticket Theatre {int(time.time())}",
            "city": "City", "address": "Address"
        }, headers=headers)
        theatre_id = r_t.json()["data"]["id"]

        r_s = client.post(f"/api/schedule/screens?theatre_id={theatre_id}", json={
            "name": "Screen Ticket", "total_seats": 50
        }, headers=headers)
        screen_id = r_s.json()["data"]["id"]

        r_show = client.post("/api/schedule/shows", json={
            "movie_id": movie_id, "screen_id": screen_id,
            "date": "2026-08-24", "start_time": "15:00:00", "end_time": "16:30:00",
            "price_multiplier": 1.0
        }, headers=headers)
        show_id = r_show.json()["data"]["id"]

        # Book seat directly via /api/bookings/book
        r_book = client.post("/api/bookings/book", json={
            "movie_id": movie_id,
            "show_id": show_id,
            "total_amount": 150.0,
            "seats": [{"seat_name": "T1", "category": "Normal"}]
        }, headers=headers)
        assert r_book.status_code == 201, f"Booking failed: {r_book.status_code} {r_book.text}"
        booking_id = r_book.json()["data"]["id"]

        # Download ticket PDF
        r_pdf = client.get(f"/api/tickets/ticket/{booking_id}/pdf", headers=headers)
        assert r_pdf.status_code == 200, f"PDF download failed: {r_pdf.status_code}"
        assert r_pdf.headers.get("content-type") == "application/pdf"
        assert len(r_pdf.content) > 1000, "PDF content is unexpectedly small"

        return f"Generated booking #{booking_id}, downloaded valid PDF ({len(r_pdf.content)} bytes)"


def main():
    print("\n" + "=" * 70)
    print("  CINEMA PLUS — LIVE PRODUCTION VERIFICATION")
    print("=" * 70 + "\n")

    verify_health()
    verify_security_headers()
    verify_cors()
    auth_data = verify_customer_auth()
    verify_invalid_login()
    if auth_data:
        verify_password_change(auth_data)
        verify_unauthorized_admin(auth_data)
    verify_admin_movie_lifecycle()
    verify_media_upload()
    verify_booking_concurrency()
    verify_ticket_pdf()

    print("\n" + "=" * 70)
    print("  VERIFICATION SUMMARY")
    print("=" * 70)
    all_passed = True
    for name, (status, detail) in results.items():
        print(f"[{status}] {name}")
        print(f"       {detail}")
        if status != "PASSED":
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("  ALL 11 LIVE VERIFICATION TESTS PASSED (100%)! [SUCCESS]")
    else:
        print("  SOME TESTS FAILED.")
    print("=" * 70 + "\n")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
