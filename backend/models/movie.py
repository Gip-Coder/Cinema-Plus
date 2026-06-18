from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    genre = Column(String(100))
    language = Column(String(100))
    format = Column(String(50))
    release_date = Column(Date)
    running_days = Column(Integer)
    poster_url = Column(String(500), nullable=True)
    poster_source_type = Column(String(50), default="upload", nullable=False)
    poster_uploaded_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer) # in minutes
    rating = Column(Float, nullable=True)

    bookings = relationship("Booking", back_populates="movie")
    shows = relationship("Show", back_populates="movie")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
