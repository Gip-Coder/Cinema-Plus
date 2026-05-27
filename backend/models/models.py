from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(20), default="customer") # 'admin' or 'customer'

    bookings = relationship("Booking", back_populates="user")
    reviews = relationship("Review", back_populates="user")

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
    description = Column(Text, nullable=True)
    duration = Column(Integer) # in minutes
    rating = Column(Float, nullable=True)

    bookings = relationship("Booking", back_populates="movie")
    shows = relationship("Show", back_populates="movie")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=True)
    total_amount = Column(Float)
    booking_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="confirmed") # confirmed or cancelled

    user = relationship("User", back_populates="bookings")
    movie = relationship("Movie", back_populates="bookings")
    show = relationship("Show", back_populates="bookings")
    booked_seats = relationship("BookedSeat", back_populates="booking", cascade="all, delete-orphan")

class BookedSeat(Base):
    __tablename__ = "booked_seats"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    show_id = Column(Integer, ForeignKey("shows.id"), nullable=True)
    seat_name = Column(String(10)) # e.g., A1, B2
    category = Column(String(50)) # Premium, Executive, Normal

    booking = relationship("Booking", back_populates="booked_seats")

class Theatre(Base):
    __tablename__ = "theatres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    location = Column(String(200))
    screens = relationship("Screen", back_populates="theatre")

class Screen(Base):
    __tablename__ = "screens"
    id = Column(Integer, primary_key=True, index=True)
    theatre_id = Column(Integer, ForeignKey("theatres.id"))
    name = Column(String(50))
    theatre = relationship("Theatre", back_populates="screens")
    shows = relationship("Show", back_populates="screen")

class Show(Base):
    __tablename__ = "shows"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    screen_id = Column(Integer, ForeignKey("screens.id"))
    start_time = Column(String(20))
    end_time = Column(String(20))
    date = Column(Date)
    price_multiplier = Column(Float, default=1.0)
    
    movie = relationship("Movie", back_populates="shows")
    screen = relationship("Screen", back_populates="shows")
    bookings = relationship("Booking", back_populates="show")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer) # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    movie = relationship("Movie", back_populates="reviews")
