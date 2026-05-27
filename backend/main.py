from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import engine, Base, SessionLocal
from backend.models import models
from backend.routes import auth_routes, movie_routes, booking_routes, ticket_routes, admin_routes, schedule_routes, review_routes
from backend.auth.security import get_password_hash
import os

app = FastAPI(title="Cinema Plus API", version="1.0.0")

# Mount static files
os.makedirs("backend/uploads/posters", exist_ok=True)
app.mount("/static/posters", StaticFiles(directory="backend/uploads/posters"), name="posters")

# CORS setup
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
    # Create tables asynchronously relative to module import
    Base.metadata.create_all(bind=engine)
    
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
