from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Any
from backend.models.models import Booking, BookedSeat, Show


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: int) -> Optional[Booking]:
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_by_id_with_relations(self, booking_id: int) -> Optional[Booking]:
        return (
            self.db.query(Booking)
            .options(
                joinedload(Booking.user),
                joinedload(Booking.movie),
                joinedload(Booking.show),
            )
            .filter(Booking.id == booking_id)
            .first()
        )

    def get_booked_seats(self, show_id: int) -> List[BookedSeat]:
        return self.db.query(BookedSeat).filter(BookedSeat.show_id == show_id).all()

    def get_existing_booked_seats(
        self,
        seat_names: List[str],
        show_id: Optional[int] = None,
        movie_id: Optional[int] = None,
    ) -> List[BookedSeat]:
        query = self.db.query(BookedSeat).filter(BookedSeat.seat_name.in_(seat_names))
        if show_id:
            query = query.filter(BookedSeat.show_id == show_id)
        else:
            query = query.filter(BookedSeat.movie_id == movie_id)
        return query.all()

    def get_user_bookings(self, user_id: int) -> List[Booking]:
        return (
            self.db.query(Booking)
            .options(
                joinedload(Booking.movie),
                joinedload(Booking.show).joinedload(Show.screen),
                selectinload(Booking.booked_seats),
            )
            .filter(Booking.user_id == user_id)
            .order_by(Booking.booking_date.desc())
            .all()
        )

    def get_all_bookings(self, skip: int = 0, limit: int = 100) -> List[Booking]:
        return (
            self.db.query(Booking)
            .options(
                joinedload(Booking.movie),
                joinedload(Booking.show).joinedload(Show.screen),
                selectinload(Booking.booked_seats),
            )
            .order_by(Booking.booking_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def stage(self, booking: Booking) -> Booking:
        """Add booking to the session WITHOUT committing.

        Use this to stage the booking so it gets an ID via flush(),
        then add all booked seats, then call commit_transaction() once.
        This prevents the booking from being visible to other connections
        before seats are attached.
        """
        self.db.add(booking)
        return booking

    def flush(self) -> None:
        """Flush pending changes to the DB to assign IDs without committing."""
        self.db.flush()

    def add_booked_seat(self, seat: BookedSeat) -> None:
        self.db.add(seat)

    def commit_transaction(self) -> None:
        """Commit the entire booking + seats as a single atomic transaction."""
        self.db.commit()

    def refresh(self, obj: Any) -> None:
        self.db.refresh(obj)

    def commit(self) -> None:
        """Alias for commit_transaction() for backward compatibility."""
        self.db.commit()

    def delete(self, booking: Booking) -> None:
        self.db.delete(booking)
        self.db.commit()

    def delete_booked_seats_by_booking_id(self, booking_id: int) -> int:
        deleted = (
            self.db.query(BookedSeat)
            .filter(BookedSeat.booking_id == booking_id)
            .delete()
        )
        self.db.commit()
        return deleted
