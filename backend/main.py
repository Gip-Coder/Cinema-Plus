from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

import os
import time
import threading
import uuid
import sys
from datetime import datetime, timezone

from backend.database import engine, Base, SessionLocal, get_db
from backend.models import models
from backend.routes import (
    auth_routes,
    movie_routes,
    booking_routes,
    ticket_routes,
    admin_routes,
    schedule_routes,
    review_routes,
    reservation_routes,
    layout_routes,
)
from backend.auth.security import get_password_hash
from backend.core.config import settings
from backend.exceptions.base import CinemaPlusException


# ── Upload directories ─────────────────────────────────────────────────────────
os.makedirs("uploads/posters", exist_ok=True)
os.makedirs("uploads/banners", exist_ok=True)
os.makedirs("uploads/defaults", exist_ok=True)
os.makedirs("uploads/media/original", exist_ok=True)
os.makedirs("uploads/media/medium", exist_ok=True)
os.makedirs("uploads/media/thumbnails", exist_ok=True)


# ── Per-request query counter ──────────────────────────────────────────────────
thread_local = threading.local()


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if hasattr(thread_local, "query_count"):
        thread_local.query_count += 1


# ── Security headers middleware ────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"  # Modern browsers use CSP instead
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response


# ── Request logging middleware ─────────────────────────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        thread_local.query_count = 0
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        query_count = getattr(thread_local, "query_count", 0)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Query-Count"] = str(query_count)

        # Log at INFO level — NOTE: never log query params that may contain passwords
        print(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} | queries={query_count} | {duration_ms:.1f}ms"
        )
        return response


# ── Admin bootstrap ────────────────────────────────────────────────────────────
# NOTE: Migrations are NOT run from this process. The production startup
# command (Dockerfile CMD / Procfile: `alembic upgrade head && uvicorn ...`)
# and the documented local dev flow (README: run `alembic upgrade head`
# before `uvicorn --reload`) both already guarantee the schema is at head
# before this app starts accepting traffic. A prior in-process
# `_run_migrations()` call here duplicated that work on every boot and
# silently swallowed migration failures (caught exception, stderr-only log),
# which could let the app start against a broken schema. Removed in favor of
# the single, fail-loud mechanism in the startup command.
def _bootstrap_admin(db: Session) -> None:
    """Create initial admin user if one does not already exist.

    The admin password MUST come from the ADMIN_PASSWORD environment variable.
    In production, the application will refuse to start if ADMIN_PASSWORD is not set.
    In development, a warning is printed and a temporary insecure password is used.
    """
    try:
        existing_admin = db.query(models.User).filter(models.User.username == "admin").first()
    except Exception as e:
        print(
            f"[BOOTSTRAP INFO] Users table not ready yet ({e}). "
            "Admin bootstrap will be skipped until migrations are applied.",
            file=sys.stderr,
        )
        return

    if existing_admin:
        return  # Admin already exists — do not touch it

    admin_password = settings.ADMIN_PASSWORD

    if not admin_password:
        if settings.is_production:
            raise RuntimeError(
                "[STARTUP ERROR] ADMIN_PASSWORD environment variable is not set. "
                "Cannot create initial admin account without it in production. "
                "Set ADMIN_PASSWORD in your environment configuration."
            )
        # Development-only fallback — loud warning
        print(
            "\n" + "=" * 70 + "\n"
            "[WARNING] ADMIN_PASSWORD is not set.\n"
            "  Creating development admin with temporary password: dev-admin-change-me\n"
            "  THIS MUST NEVER HAPPEN IN PRODUCTION.\n"
            "  Set ADMIN_PASSWORD in your .env file.\n"
            + "=" * 70 + "\n",
            file=sys.stderr,
        )
        admin_password = "dev-admin-change-me"

    print("Creating initial admin user...")
    hashed_pw = get_password_hash(admin_password)
    new_admin = models.User(
        username="admin",
        email=settings.ADMIN_EMAIL,
        hashed_password=hashed_pw,
        role="admin",
    )
    db.add(new_admin)
    db.commit()
    print(f"Admin user created with email: {settings.ADMIN_EMAIL}")


# ── Lifespan (replaces deprecated @app.on_event) ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1. Validate production config before accepting any traffic
    try:
        settings.validate_production_config()
    except RuntimeError as e:
        print(f"\n{e}\n", file=sys.stderr)
        sys.exit(1)

    # 2. Bootstrap admin account
    db = SessionLocal()
    try:
        _bootstrap_admin(db)
    except RuntimeError as e:
        print(f"\n{e}\n", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

    yield  # Application runs here

    # Shutdown tasks (add any cleanup here)
    print("Cinema Plus API shutting down.")


# ── FastAPI Application ────────────────────────────────────────────────────────
# Disable interactive docs AND the raw OpenAPI schema in production unless
# explicitly enabled. Disabling only docs_url/redoc_url leaves /openapi.json
# reachable by default (FastAPI's own default for openapi_url is unaffected
# by docs_url/redoc_url), which still exposes every route/model shape.
_docs_enabled = not settings.is_production or settings.ENABLE_DOCS
_docs_url = "/docs" if _docs_enabled else None
_redoc_url = "/redoc" if _docs_enabled else None
_openapi_url = "/openapi.json" if _docs_enabled else None

app = FastAPI(
    title="Cinema Plus API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

# ── Static files ───────────────────────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Middleware (order matters — outermost runs first/last) ─────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms", "X-Query-Count"],
)


# ── Exception handlers ─────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    err_msgs = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err["loc"])
        msg = err["msg"]
        err_msgs.append(f"{loc}: {msg}")
    detail_msg = "Validation Error: " + "; ".join(err_msgs)
    print(f"[VALIDATION ERROR] {request.method} {request.url.path} | {detail_msg}")

    serializable_errors = []
    for err in errors:
        cleaned_err = dict(err)
        if "ctx" in cleaned_err and isinstance(cleaned_err["ctx"], dict):
            cleaned_err["ctx"] = {
                k: str(v) if isinstance(v, Exception) else v
                for k, v in cleaned_err["ctx"].items()
            }
        serializable_errors.append(cleaned_err)

    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={"detail": detail_msg, "errors": serializable_errors},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    # Log the real error internally but return a safe message to clients
    print(f"[DATABASE ERROR] {request.method} {request.url.path} | {type(exc).__name__}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again later."},
    )


@app.exception_handler(CinemaPlusException)
async def cinemaplus_exception_handler(request: Request, exc: CinemaPlusException):
    print(f"[API ERROR] {request.method} {request.url.path} | {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(movie_routes.router, prefix="/api/movies", tags=["Movies"])
app.include_router(booking_routes.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(ticket_routes.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Admin"])
app.include_router(schedule_routes.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(review_routes.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(reservation_routes.router, prefix="/api", tags=["Reservations"])
app.include_router(layout_routes.router, prefix="/api/layouts", tags=["Layouts"])


# ── Root / health endpoints ────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Cinema Plus API", "status": "running", "version": "1.0.0"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "database": "ok",
        "storage": "ok",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["database"] = "error"
        health_status["status"] = "unhealthy"
        print(f"[HEALTH] Database check failed: {type(e).__name__}")

    try:
        os.makedirs("uploads", exist_ok=True)
        test_file = os.path.join("uploads", ".health_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        health_status["storage"] = "error"
        health_status["status"] = "unhealthy"
        print(f"[HEALTH] Storage check failed: {type(e).__name__}")

    if health_status["status"] == "unhealthy":
        return JSONResponse(status_code=503, content=health_status)
    return health_status
