import json
from datetime import datetime, timezone
from typing import Callable, Dict, List, Any
from sqlalchemy.orm import Session
from backend.models.models import AuditLog

class EventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, listener: Callable[[Session, Any], None]):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def dispatch(self, db: Session, event_type: str, data: Any):
        print(f"[EVENT] Dispatching {event_type} with data: {data}")
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    listener(db, data)
                except Exception as e:
                    print(f"[EVENT ERROR] Error in listener for {event_type}: {e}")

dispatcher = EventDispatcher()

# Event schemas/definitions
class ReservationEvent:
    def __init__(self, group_id: int, user_id: int, show_id: int, seats: List[str]):
        self.group_id = group_id
        self.user_id = user_id
        self.show_id = show_id
        self.seats = seats

class BookingEvent:
    def __init__(self, booking_id: int, user_id: int, show_id: int, seats: List[str], total_amount: float):
        self.booking_id = booking_id
        self.user_id = user_id
        self.show_id = show_id
        self.seats = seats
        self.total_amount = total_amount

# Hook up default audit logging listeners
def log_reservation_created(db: Session, event: ReservationEvent):
    log = AuditLog(
        user_id=event.user_id,
        entity_type="reservation_group",
        entity_id=event.group_id,
        action="Reservation Created",
        new_value=json.dumps({"show_id": event.show_id, "seats": event.seats}),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

def log_reservation_cancelled(db: Session, event: ReservationEvent):
    log = AuditLog(
        user_id=event.user_id,
        entity_type="reservation_group",
        entity_id=event.group_id,
        action="Reservation Cancelled",
        old_value=json.dumps({"show_id": event.show_id, "seats": event.seats}),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

def log_reservation_expired(db: Session, event: ReservationEvent):
    log = AuditLog(
        user_id=event.user_id,
        entity_type="reservation_group",
        entity_id=event.group_id,
        action="Reservation Expired",
        old_value=json.dumps({"show_id": event.show_id, "seats": event.seats}),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

def log_reservation_confirmed(db: Session, event: ReservationEvent):
    log = AuditLog(
        user_id=event.user_id,
        entity_type="reservation_group",
        entity_id=event.group_id,
        action="Reservation Confirmed",
        new_value=json.dumps({"show_id": event.show_id, "seats": event.seats}),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

def log_booking_created(db: Session, event: BookingEvent):
    log = AuditLog(
        user_id=event.user_id,
        entity_type="booking",
        entity_id=event.booking_id,
        action="Booking Created",
        new_value=json.dumps({"show_id": event.show_id, "seats": event.seats, "total_amount": event.total_amount}),
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

# Register listeners
dispatcher.subscribe("ReservationCreated", log_reservation_created)
dispatcher.subscribe("ReservationCancelled", log_reservation_cancelled)
dispatcher.subscribe("ReservationExpired", log_reservation_expired)
dispatcher.subscribe("ReservationConfirmed", log_reservation_confirmed)
dispatcher.subscribe("BookingCreated", log_booking_created)
