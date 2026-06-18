from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Text, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

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
