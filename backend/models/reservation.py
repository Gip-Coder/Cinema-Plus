from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class ReservationGroup(Base):
    __tablename__ = "reservation_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    show_id = Column(Integer, ForeignKey("shows.id"), index=True)
    reservation_token = Column(String(100), nullable=False)
    reserved_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="active", index=True) # active, expired, converted, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    show = relationship("Show")
    reserved_seats = relationship("SeatReservation", back_populates="reservation_group", cascade="all, delete-orphan")

class SeatReservation(Base):
    __tablename__ = "seat_reservations"

    id = Column(Integer, primary_key=True, index=True)
    reservation_group_id = Column(Integer, ForeignKey("reservation_groups.id"), index=True)
    seat_id = Column(String(10), index=True) # e.g. 'A1'
    show_id = Column(Integer, ForeignKey("shows.id"), index=True)
    status = Column(String(20), default="active", index=True) # active, expired, converted, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    reservation_group = relationship("ReservationGroup", back_populates="reserved_seats")
    show = relationship("Show")
