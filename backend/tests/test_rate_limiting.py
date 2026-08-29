import pytest
from fastapi import status

from backend.utils.rate_limiter import rate_limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def test_login_rate_limit_blocks_after_threshold_then_recovers(client):
    from backend.utils import rate_limiter as rl_module

    bad_login = {"username": "admin", "password": "wrong-password"}

    statuses = []
    for _ in range(rl_module.LOGIN_MAX_ATTEMPTS + 3):
        res = client.post("/api/auth/login", json=bad_login)
        statuses.append(res.status_code)

    assert status.HTTP_429_TOO_MANY_REQUESTS in statuses, (
        f"expected a 429 once the login rate limit was exceeded, got {statuses}"
    )
    # Everything before the limit kicked in should be a normal auth failure
    # (401), never a 500 — legitimate retries must not be broken.
    assert all(s in (status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS) for s in statuses)

    rate_limiter.reset()

    # A legitimate login immediately after a reset (simulating the window
    # having elapsed) must succeed normally — the limiter must not
    # permanently lock out a client.
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == status.HTTP_200_OK


def test_register_rate_limit_blocks_after_threshold(client):
    from backend.utils import rate_limiter as rl_module

    statuses = []
    for i in range(rl_module.REGISTER_MAX_ATTEMPTS + 2):
        res = client.post(
            "/api/auth/register",
            json={
                "username": f"rl_test_user_{i}",
                "email": f"rl_test_user_{i}@example.com",
                "password": "testpassword123",
            },
        )
        statuses.append(res.status_code)

    assert status.HTTP_429_TOO_MANY_REQUESTS in statuses, (
        f"expected a 429 once the register rate limit was exceeded, got {statuses}"
    )
    # Requests before the limit was hit should have succeeded normally.
    assert status.HTTP_201_CREATED in statuses


def test_legitimate_login_succeeds_under_the_limit(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == status.HTTP_200_OK
