from fastapi import status

from backend.core.config import settings


def _admin_headers(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == status.HTTP_200_OK
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_health_reports_real_database_status_not_the_old_bug(client):
    """Regression test for the bug where get_system_health() called
    `self.db.execute(func.select(1))` instead of a real SELECT statement,
    which always raised and always reported "unhealthy" / 0ms latency
    regardless of actual database health, and mislabeled the engine as
    a hardcoded "PostgreSQL Pool" in the frontend even though this project
    only ever runs MySQL (production) / SQLite (tests)."""
    headers = _admin_headers(client)
    res = client.get("/api/admin/health", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()["data"]

    assert data["database"]["status"] == "healthy"
    assert data["database"]["latency_ms"] >= 0
    # Must reflect the real bound engine, never a hardcoded "postgresql".
    assert data["database"]["engine"] in ("sqlite", "mysql")
    assert data["database"]["engine"] != "postgresql"


def test_admin_health_storage_check_is_real(client):
    headers = _admin_headers(client)
    res = client.get("/api/admin/health", headers=headers)
    data = res.json()["data"]

    assert "storage" in data
    assert data["storage"]["status"] == "healthy"
    assert data["storage"]["path"] == "uploads/"


def test_admin_health_reservation_status_reflects_real_config(client):
    headers = _admin_headers(client)
    res = client.get("/api/admin/health", headers=headers)
    data = res.json()["data"]

    assert data["reservation"]["mechanism"] == "database_unique_constraint"
    assert data["reservation"]["hold_minutes"] == settings.RESERVATION_TIMEOUT_MINUTES


def test_admin_health_scheduler_tasks_are_honest_not_fabricated():
    """None of these are real scheduled jobs — there is no
    APScheduler/Celery/cron/periodic task anywhere in this codebase. The
    dashboard must say so rather than claiming ACTIVE/IDLE."""
    import backend.services.admin_service as admin_service_module
    import inspect

    source = inspect.getsource(admin_service_module.AdminService.get_system_health)
    assert "not_configured" in source
    assert "on_demand" in source


def test_admin_health_requires_admin_role(client):
    res = client.post(
        "/api/auth/register",
        json={"username": "health_probe_user", "email": "health_probe_user@example.com", "password": "testpassword123"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    login = client.post("/api/auth/login", json={"username": "health_probe_user", "password": "testpassword123"})
    token = login.json()["data"]["access_token"]

    res = client.get("/api/admin/health", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == status.HTTP_403_FORBIDDEN
