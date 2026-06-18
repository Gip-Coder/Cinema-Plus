from fastapi import FastAPI, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from backend.database import engine, Base, SessionLocal, get_db
from backend.models import models
from backend.routes import auth_routes, movie_routes, booking_routes, ticket_routes, admin_routes, schedule_routes, review_routes, reservation_routes, layout_routes
from backend.auth.security import get_password_hash
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import os
import time
import threading
import uuid
import json
from datetime import datetime

app = FastAPI(title="Cinema Plus API", version="1.0.0")

# Mount uploads static files (Task 5: unified static mount)
os.makedirs("uploads/posters", exist_ok=True)
os.makedirs("uploads/banners", exist_ok=True)
os.makedirs("uploads/defaults", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Thread-local storage to count queries executed per request
thread_local = threading.local()

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if hasattr(thread_local, "query_count"):
        thread_local.query_count += 1

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        thread_local.query_count = 0
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        query_count = getattr(thread_local, "query_count", 0)
        
        # Set performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Query-Count"] = str(query_count)
        
        # Task 11 Request Logging
        print(f"[Request {request_id}] {request.method} {request.url.path} - Status: {response.status_code} | Queries: {query_count} | Latency: {duration_ms:.2f}ms")
        return response

# Register Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Exception Handlers (Task 10)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    err_msgs = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err["loc"])
        msg = err["msg"]
        err_msgs.append(f"{loc}: {msg}")
    detail_msg = "Validation Error: " + "; ".join(err_msgs)
    print(f"[VALIDATION ERROR] Request: {request.method} {request.url.path} | {detail_msg}")
    
    # Ensure all error elements are JSON serializable (convert Exception instances in ctx to string)
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
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail_msg, "errors": serializable_errors}
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    err_msg = str(exc.__dict__.get("orig") or exc)
    print(f"[DATABASE ERROR] Request: {request.method} {request.url.path} | Error: {err_msg}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Database transaction failed: {err_msg}"}
    )

from backend.exceptions.base import CinemaPlusException

@app.exception_handler(CinemaPlusException)
async def cinemaplus_exception_handler(request: Request, exc: CinemaPlusException):
    print(f"[API ERROR] Request: {request.method} {request.url.path} | Error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(movie_routes.router, prefix="/api/movies", tags=["Movies"])
app.include_router(booking_routes.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(ticket_routes.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Admin"])
app.include_router(schedule_routes.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(review_routes.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(reservation_routes.router, prefix="/api", tags=["Reservations"])
app.include_router(layout_routes.router, prefix="/api/layouts", tags=["Layouts"])


# Application startup logic
# pyrefly: ignore [deprecated]
@app.on_event("startup")
def startup_event():
    # Base.metadata.create_all(bind=engine) # Handled by Alembic migrations now
    
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            print("Creating initial admin user...")
            hashed_pw = get_password_hash("admin123")
            new_admin = models.User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed_pw,
                role="admin"
            )
            db.add(new_admin)
            db.commit()
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Welcome to the Movie Ticket Booking API!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "database": "ok",
        "storage": "ok",
        "version": "1.0.0",
        # pyrefly: ignore [deprecated]
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Check Database connectivity
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        
    # Check Storage accessibility
    try:
        os.makedirs("uploads", exist_ok=True)
        test_file = os.path.join("uploads", ".health_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        health_status["storage"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        
    if health_status["status"] == "unhealthy":
        return JSONResponse(status_code=503, content=health_status)
    return health_status
