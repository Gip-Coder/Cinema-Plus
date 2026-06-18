from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Any
from backend.models.models import Booking, BookedSeat, Show

class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, booking_id: int) -> Optional[Booking]:
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_by_id_with_relations(self, booking_id: int) -> Optional[Booking]:
        return self.db.query(Booking).options(
            joinedload(Booking.user),
            joinedload(Booking.movie),
            joinedload(Booking.show)
        ).filter(Booking.id == booking_id).first()

    def get_booked_seats(self, show_id: int) -> List[BookedSeat]:
        return self.db.query(BookedSeat).filter(BookedSeat.show_id == show_id).all()

    def get_existing_booked_seats(self, seat_names: List[str], show_id: Optional[int] = None, movie_id: Optional[int] = None) -> List[BookedSeat]:
        query = self.db.query(BookedSeat).filter(BookedSeat.seat_name.in_(seat_names))
        if show_id:
            query = query.filter(BookedSeat.show_id == show_id)
        else:
            query = query.filter(BookedSeat.movie_id == movie_id)
        return query.all()

    def get_user_bookings(self, user_id: int) -> List[Booking]:
        return self.db.query(Booking).options(
            joinedload(Booking.movie),
            joinedload(Booking.show).joinedload(Show.screen),
            selectinload(Booking.booked_seats)
        ).filter(Booking.user_id == user_id).order_by(Booking.booking_date.desc()).all()

    def get_all_bookings(self, skip: int = 0, limit: int = 100) -> List[Booking]:
        return self.db.query(Booking).options(
            joinedload(Booking.movie),
            joinedload(Booking.show).joinedload(Show.screen),
            selectinload(Booking.booked_seats)
        ).order_by(Booking.booking_date.desc()).offset(skip).limit(limit).all()

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def add_booked_seat(self, seat: BookedSeat) -> None:
        self.db.add(seat)

    def commit(self) -> None:
        self.db.commit()

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, obj: Any) -> None:
        self.db.refresh(obj)

    def delete(self, booking: Booking) -> None:
        self.db.delete(booking)
        self.db.commit()

    def delete_booked_seats_by_booking_id(self, booking_id: int) -> int:
        deleted = self.db.query(BookedSeat).filter(BookedSeat.booking_id == booking_id).delete()
        self.db.commit()
        return deleted
