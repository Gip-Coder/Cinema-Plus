from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DDL, event
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


# Guarantees only one "active" hold can exist per (show_id, seat_id) at a time,
# enforced at the DB layer so a race between two concurrent reservation
# requests can never both succeed. This only fires when SeatReservation's
# table is freshly created by `Base.metadata.create_all()` (used by the test
# suite and by scripts/seed_db.py) — the real production path applies the
# equivalent DDL via Alembic migration f3a1c9b8d2e4, which also runs against
# databases that already have data.
#
# MySQL has no partial/filtered unique index, so it needs the generated-column
# workaround (see the migration for the full rationale). SQLite supports a
# real partial unique index directly, which gives an equivalent guarantee for
# the pytest suite without needing the generated column at all.
_mysql_active_lock_ddl = DDL(
    "ALTER TABLE seat_reservations "
    "ADD COLUMN active_lock_key VARCHAR(30) "
    "GENERATED ALWAYS AS (IF(status = 'active', CONCAT(show_id, ':', seat_id), NULL)) STORED, "
    "ADD UNIQUE INDEX uq_seat_reservations_active_lock (active_lock_key)"
)
event.listen(
    SeatReservation.__table__,
    "after_create",
    _mysql_active_lock_ddl.execute_if(dialect="mysql"),
)

_sqlite_active_lock_ddl = DDL(
    "CREATE UNIQUE INDEX uq_seat_reservations_active_lock "
    "ON seat_reservations (show_id, seat_id) WHERE status = 'active'"
)
event.listen(
    SeatReservation.__table__,
    "after_create",
    _sqlite_active_lock_ddl.execute_if(dialect="sqlite"),
)
