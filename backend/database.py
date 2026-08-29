import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from backend.core.config import settings

# ── Testing mode ───────────────────────────────────────────────────────────────
TESTING_MODE = os.getenv("TESTING") == "True"

if TESTING_MODE:
    # In-memory SQLite, not a file on disk. GitHub Actions' ubuntu-latest
    # runners have consistently failed on the file-based `sqlite:///./test.db`
    # with `sqlite3.OperationalError: disk I/O error` during the very first
    # CREATE TABLE — a low-level filesystem I/O failure, not an application
    # bug (confirmed: every run of this CI workflow has failed the same way
    # since its first run, across unrelated commits). Moving the test
    # database off the filesystem entirely avoids that class of failure.
    #
    # StaticPool hands every SessionLocal() call the SAME physical sqlite3
    # connection object, which is fine for ordinary sequential test code.
    # backend/tests/test_reservation_concurrency.py deliberately opens two
    # sessions in two separate threads to test a genuine concurrent-booking
    # race, which needs two REAL independent connections — that test uses
    # its own dedicated, narrowly-scoped temp-file SQLite engine instead
    # (see that file), rather than sharing this in-memory engine. (A SQLite
    # shared-cache in-memory URI was also tried for that test as an
    # alternative to a temp file — it produces `database table is locked`
    # errors that, unlike ordinary file-level SQLite locks, are NOT retried
    # by busy_timeout, making it unreliable for genuinely concurrent
    # writers. Reverted in favor of the temp-file approach.)
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    print("Testing mode: Connecting to in-memory SQLite database.")
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    # Log connection info without the password
    _safe_url = (
        f"mysql+pymysql://{settings.DB_USER}:***"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    print(f"Connecting to database: {_safe_url}")
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

# ── Verify connectivity ────────────────────────────────────────────────────────
try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"Database connection OK. Tables found: {len(existing_tables)}")

        required_tables = ["movies", "bookings", "theatres", "screens", "users"]
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            print(
                f"[WARNING] Required tables are missing: {missing_tables}. "
                "Run 'alembic upgrade head' to apply migrations."
            )
        else:
            print("All required tables verified.")

except Exception as e:
    # Print a safe error message (no URL with password in traceback)
    print(f"[DATABASE CONNECTION ERROR] {type(e).__name__}: {e}", file=sys.stderr)
    if TESTING_MODE:
        print("Testing mode: Bypassing database connection failure.")
    else:
        print(
            "Application startup aborted: cannot connect to the database.\n"
            "Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME in your environment.",
            file=sys.stderr,
        )
        sys.exit(1)

# ── Session factory ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
