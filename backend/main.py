from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from backend.database import engine, Base, SessionLocal
from backend.models import models
from backend.routes import auth_routes, movie_routes, booking_routes, ticket_routes, admin_routes, schedule_routes, review_routes
from backend.auth.security import get_password_hash
from sqlalchemy import event
import os
import time
import threading

app = FastAPI(title="Cinema Plus API", version="1.0.0")

# Mount uploads static files
os.makedirs("backend/uploads/posters", exist_ok=True)
os.makedirs("uploads/posters", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Thread-local storage to count queries executed per request
thread_local = threading.local()

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if hasattr(thread_local, "query_count"):
        thread_local.query_count += 1

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        thread_local.query_count = 0
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        query_count = getattr(thread_local, "query_count", 0)
        
        # Set performance headers
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        response.headers["X-Query-Count"] = str(query_count)
        
        print(f"[{request.method}] {request.url.path} - {response.status_code} | Queries: {query_count} | Latency: {duration_ms:.2f}ms")
        return response

# Register Middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(movie_routes.router, prefix="/api/movies", tags=["Movies"])
app.include_router(booking_routes.router, prefix="/api/bookings", tags=["Bookings"])
app.include_router(ticket_routes.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Admin"])
app.include_router(schedule_routes.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(review_routes.router, prefix="/api/reviews", tags=["Reviews"])

# Application startup logic
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
