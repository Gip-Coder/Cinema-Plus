from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict
from backend.models.booking import BookedSeat, Booking
from backend.models.reservation import SeatReservation, ReservationGroup

class SeatStateService:
    def __init__(self, db: Session):
        self.db = db

    def get_seat_statuses(self, show_id: int) -> Dict[str, List[str]]:
        """
        Returns a dict of:
        {
            "booked": [seat_names],
            "reserved": [seat_names]
        }
        """
        # Get booked seats (only for confirmed/active bookings)
        booked_query = (
            self.db.query(BookedSeat.seat_name)
            .join(Booking, BookedSeat.booking_id == Booking.id)
            .filter(BookedSeat.show_id == show_id)
            .filter(Booking.status != "cancelled")
            .all()
        )
        booked_seats = [row[0] for row in booked_query]

        # Get reserved seats (active unexpired reservations)
        now = datetime.utcnow()
        reserved_query = (
            self.db.query(SeatReservation.seat_id)
            .join(ReservationGroup, SeatReservation.reservation_group_id == ReservationGroup.id)
            .filter(SeatReservation.show_id == show_id)
            .filter(ReservationGroup.status == "active")
            .filter(ReservationGroup.expires_at > now)
            .filter(SeatReservation.status == "active")
            .all()
        )
        reserved_seats = [row[0] for row in reserved_query]

        return {
            "booked": booked_seats,
            "reserved": reserved_seats
        }

    def check_availability(self, show_id: int, seat_names: List[str]) -> bool:
        """
        Checks if all target seats are currently free (neither booked nor reserved).
        """
        statuses = self.get_seat_statuses(show_id)
        taken_seats = set(statuses["booked"] + statuses["reserved"])
        
        for seat in seat_names:
            if seat in taken_seats:
                return False
        return True
