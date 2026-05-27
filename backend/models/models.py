from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Text, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default="customer") # 'admin', 'theatre_manager', 'staff', 'customer'

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

class Theatre(Base):
    __tablename__ = "theatres"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    timezone = Column(String(50), default="UTC")
    contact_info = Column(String(200))
    description = Column(Text)
    banner_image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    screens = relationship("Screen", back_populates="theatre", cascade="all, delete-orphan")

class Screen(Base):
    __tablename__ = "screens"
    id = Column(Integer, primary_key=True, index=True)
    theatre_id = Column(Integer, ForeignKey("theatres.id"), index=True)
    name = Column(String(50), nullable=False)
    screen_type = Column(String(50), default="Standard") # IMAX, 3D, Standard, Dolby Atmos
    total_seats = Column(Integer, default=220)
    seat_layout_json = Column(Text) # JSON string representation
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    theatre = relationship("Theatre", back_populates="screens")
    shows = relationship("Show", back_populates="screen", cascade="all, delete-orphan")

class Show(Base):
    __tablename__ = "shows"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), index=True)
    screen_id = Column(Integer, ForeignKey("screens.id"))
    start_time = Column(String(20))
    end_time = Column(String(20))
    date = Column(Date, index=True)
    price_multiplier = Column(Float, default=1.0)
    
    movie = relationship("Movie", back_populates="shows")
    screen = relationship("Screen", back_populates="shows")
    bookings = relationship("Booking", back_populates="show")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    rating = Column(Integer) # 1-5
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    movie = relationship("Movie", back_populates="reviews")

class SeatPricing(Base):
    __tablename__ = "seat_pricings"
    id = Column(Integer, primary_key=True, index=True)
    theatre_id = Column(Integer, ForeignKey("theatres.id"), index=True)
    screen_id = Column(Integer, ForeignKey("screens.id"), nullable=True, index=True)
    seat_category = Column(String(50), index=True) # Premium, Executive, Normal
    base_price = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PricingRule(Base):
    __tablename__ = "pricing_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rule_type = Column(String(50), index=True) # weekend, holiday, event, surge, time_based
    multiplier = Column(Float, nullable=False, default=1.0)
    priority = Column(Integer, default=0)
    stackable = Column(Boolean, default=True)
    valid_from = Column(Date)
    valid_to = Column(Date)
    is_active = Column(Boolean, default=True)
    theatre_id = Column(Integer, ForeignKey("theatres.id"), nullable=True, index=True)
    screen_id = Column(Integer, ForeignKey("screens.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MediaAsset(Base):
    __tablename__ = "media_assets"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    storage_provider = Column(String(50), default="local") # local, s3, cdn, external
    storage_key = Column(String(255))
    public_url = Column(String(1000))
    mime_type = Column(String(100))
    size_bytes = Column(Integer)
    asset_type = Column(String(50)) # poster, banner, screen_preview
    thumbnail_url = Column(String(1000))
    medium_url = Column(String(1000))
    source_type = Column(String(50), default="upload") # upload, external_url
    original_source_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    entity_type = Column(String(50), index=True)
    entity_id = Column(Integer, index=True)
    action = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)
