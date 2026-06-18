import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.core.config import settings

# Fully migrated to MySQL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}"
print(f"Connecting to database: mysql+pymysql://{settings.DB_USER}:***@{settings.DB_HOST}/{settings.DB_NAME}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True
)

from sqlalchemy import inspect, text
import sys

try:
    with engine.connect() as connection:
        # Task 1 startup verification requirement: SELECT 1
        connection.execute(text("SELECT 1"))
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"Successfully connected to MySQL Database: {settings.DB_NAME}")
        print(f"Active Tables found: {existing_tables}")
        
        required_tables = ["movies", "bookings", "theatres", "screens", "users", "reviews"]
        missing_tables = [t for t in required_tables if t not in existing_tables]
        if missing_tables:
            print(f"WARNING: The following required tables are missing in MySQL: {missing_tables}")
        else:
            print("All required tables are verified and exist in MySQL database!")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to connect to MySQL database at startup: {e}")
    print("Application startup aborted due to database unavailability.")
    sys.exit(1)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
