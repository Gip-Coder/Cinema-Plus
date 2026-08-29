import os
import sys

# Set TESTING environment variable before importing any local packages
os.environ["TESTING"] = "True"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-long-for-testing-only"
os.environ["APP_ENV"] = "development"

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from backend.database import Base, engine, SessionLocal as TestingSessionLocal, get_db
from backend.models import models
from backend.auth.security import get_password_hash
from backend.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Clean up any old test.db first
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except Exception:
            pass
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after the test session is completed
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except Exception:
            pass


@pytest.fixture(name="db")
def db_fixture():
    session = TestingSessionLocal()

    # Ensure admin exists in this test session
    if not session.query(models.User).filter(models.User.username == "admin").first():
        admin = models.User(
            username="admin",
            email="admin@cinemaplus.test",
            hashed_password=get_password_hash("admin123"),
            role="admin",
        )
        session.add(admin)
        session.commit()

    yield session

    session.close()


@pytest.fixture(name="client")
def client_fixture(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_rate_limiter_between_tests():
    # backend.utils.rate_limiter.rate_limiter is a process-global singleton
    # (by design — see its module docstring, it mirrors the single-worker
    # production deployment). Without resetting it here, login/register
    # calls made by any earlier test in this same pytest process count
    # toward the same client-IP bucket as every later test (TestClient uses
    # a fixed "testclient" host), so the whole suite would slowly approach
    # the real rate limit and start failing tests that have nothing to do
    # with rate limiting themselves — this is what happened before this
    # fixture existed.
    from backend.utils.rate_limiter import rate_limiter

    rate_limiter.reset()
    yield
    rate_limiter.reset()
