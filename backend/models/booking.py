from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), index=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=True, index=True)
    total_amount = Column(Float)
    booking_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default="confirmed") # confirmed or cancelled

    user = relationship("User", back_populates="bookings")
    movie = relationship("Movie", back_populates="bookings")
    show = relationship("Show", back_populates="bookings")
    booked_seats = relationship("BookedSeat", back_populates="booking", cascade="all, delete-orphan")

class BookedSeat(Base):
    __tablename__ = "booked_seats"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), index=True)
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=True, index=True)
    seat_name = Column(String(10)) # e.g., A1, B2
    category = Column(String(50)) # Premium, Executive, Normal

    booking = relationship("Booking", back_populates="booked_seats")
