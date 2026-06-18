from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default="customer") # 'admin', 'theatre_manager', 'staff', 'customer'

    bookings = relationship("Booking", back_populates="user")
    reviews = relationship("Review", back_populates="user")
