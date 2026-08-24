from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import secrets
from typing import List, cast
from backend.models.reservation import ReservationGroup, SeatReservation
from backend.models.booking import Booking, BookedSeat
from backend.models.models import Show
from backend.core.config import settings
from backend.services.seat_state_service import SeatStateService
from backend.exceptions.reservation_exceptions import (
    ReservationNotFoundException,
    ReservationExpiredException,
    ReservationAlreadyConvertedException,
    SeatsAlreadyReservedException
)
from backend.exceptions.booking_exceptions import ShowNotFoundException
from backend.utils.events import dispatcher, ReservationEvent, BookingEvent
from backend.utils.pricing_engine import calculate_dynamic_price

class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.seat_state_service = SeatStateService(db)

    def cleanup_expired_reservations(self):
        """
        On-demand cleanup of expired active reservations.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expired_groups = (
            self.db.query(ReservationGroup)
            .filter(ReservationGroup.status == "active")
            .filter(ReservationGroup.expires_at <= now)
            .all()
        )
        for group in expired_groups:
            group.status = "expired"  # type: ignore
            for seat in group.reserved_seats:
                seat.status = "expired"  # type: ignore
            
            # Dispatch event
            seats = [s.seat_id for s in group.reserved_seats]
            event = ReservationEvent(cast(int, group.id), cast(int, group.user_id), cast(int, group.show_id), seats)
            dispatcher.dispatch(self.db, "ReservationExpired", event)
            
        if expired_groups:
            self.db.commit()

    def create_reservation_group(self, show_id: int, seat_names: List[str], user_id: int) -> ReservationGroup:
        # 1. Clean up expired reservations first to release seat blocks
        self.cleanup_expired_reservations()

        # 2. Check if show exists
        show = self.db.query(Show).filter(Show.id == show_id).first()
        if not show:
            raise ShowNotFoundException(show_id)

        # 3. Check seat availability (neither booked nor reserved)
        if not self.seat_state_service.check_availability(show_id, seat_names):
            raise SeatsAlreadyReservedException(seat_names)

        # 4. Create reservation session
        token = secrets.token_hex(16)
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=settings.RESERVATION_TIMEOUT_MINUTES)
        
        group = ReservationGroup(
            user_id=user_id,
            show_id=show_id,
            reservation_token=token,
            reserved_at=datetime.now(timezone.utc).replace(tzinfo=None),
            expires_at=expires_at,
            status="active"
        )
        self.db.add(group)
        self.db.flush() # get group.id

        # 5. Create individual seat reservations
        for seat_name in seat_names:
            seat_res = SeatReservation(
                reservation_group_id=group.id,
                seat_id=seat_name,
                show_id=show_id,
                status="active"
            )
            self.db.add(seat_res)
        
        self.db.commit()
        self.db.refresh(group)

        # 6. Dispatch event
        event = ReservationEvent(cast(int, group.id), user_id, show_id, seat_names)
        dispatcher.dispatch(self.db, "ReservationCreated", event)

        return group

    def cancel_reservation(self, group_id: int, user_id: int) -> ReservationGroup:
        # 1. Fetch group
        group = self.db.query(ReservationGroup).filter(ReservationGroup.id == group_id).first()
        if not group:
            raise ReservationNotFoundException(group_id)

        # 2. Authorization check
        if group.user_id != user_id:
            from backend.exceptions.base import PermissionDeniedException
            raise PermissionDeniedException("Not authorized to cancel this reservation.")

        # 3. Check if already converted or cancelled
        if group.status == "converted":
            raise ReservationAlreadyConvertedException(group_id)
        if group.status == "cancelled":
            return group

        # 4. Cancel
        group.status = "cancelled"  # type: ignore
        for seat in group.reserved_seats:
            seat.status = "cancelled"  # type: ignore
        
        self.db.commit()
        self.db.refresh(group)

        # 5. Dispatch event
        seats = [s.seat_id for s in group.reserved_seats]
        event = ReservationEvent(cast(int, group.id), user_id, cast(int, group.show_id), seats)
        dispatcher.dispatch(self.db, "ReservationCancelled", event)

        return group

    def confirm_reservation(self, group_id: int, user_id: int) -> Booking:
        # 1. Lock the reservation group row to prevent concurrent modification
        group = (
            self.db.query(ReservationGroup)
            .filter(ReservationGroup.id == group_id)
            .with_for_update()
            .first()
        )
        if not group:
            raise ReservationNotFoundException(group_id)

        # 2. Check authorization
        if group.user_id != user_id:
            from backend.exceptions.base import PermissionDeniedException
            raise PermissionDeniedException("Not authorized to confirm this reservation.")

        # 3. Check group status
        if group.status == "converted":
            booking = self.db.query(Booking).filter(Booking.show_id == group.show_id, Booking.user_id == user_id).order_by(Booking.id.desc()).first()
            if booking:
                return booking
            raise ReservationAlreadyConvertedException(group_id)
            
        if group.status == "cancelled":
            raise ReservationExpiredException(group_id)

        # 4. Check if group expired
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if group.expires_at <= now or group.status == "expired":
            group.status = "expired"  # type: ignore
            for seat in group.reserved_seats:
                seat.status = "expired"  # type: ignore
            self.db.commit()
            
            # Dispatch expired event
            seats = [s.seat_id for s in group.reserved_seats]
            event = ReservationEvent(cast(int, group.id), user_id, cast(int, group.show_id), seats)
            dispatcher.dispatch(self.db, "ReservationExpired", event)
            
            raise ReservationExpiredException(group_id)

        # 5. Get seat categories and prices
        show = group.show
        if not show:
            raise ShowNotFoundException(cast(int, group.show_id))

        total_amount = 0.0
        seats_payload = []
        for seat_res in group.reserved_seats:
            category = get_seat_category_for_show(self.db, cast(int, group.show_id), seat_res.seat_id)
            price_details = calculate_dynamic_price(self.db, cast(int, group.show_id), category)
            price = price_details["final_price"]
            total_amount += price
            seats_payload.append({
                "seat_name": seat_res.seat_id,
                "category": category,
                "price": price
            })

        # 6. Create booking
        booking = Booking(
            user_id=user_id,
            movie_id=show.movie_id,
            show_id=group.show_id,
            total_amount=round(total_amount, 2),
            status="confirmed"
        )
        self.db.add(booking)
        self.db.flush()

        # 7. Create booked seats
        for seat in seats_payload:
            booked_seat = BookedSeat(
                booking_id=booking.id,
                movie_id=show.movie_id,
                show_id=group.show_id,
                seat_name=seat["seat_name"],
                category=seat["category"]
            )
            self.db.add(booked_seat)

        # 8. Mark reservation as converted
        group.status = "converted"  # type: ignore
        for seat_res in group.reserved_seats:
            seat_res.status = "converted"  # type: ignore

        # Commit transaction
        self.db.commit()
        self.db.refresh(booking)

        # 9. Dispatch events
        seats_names = [s["seat_name"] for s in seats_payload]
        res_event = ReservationEvent(cast(int, group.id), user_id, cast(int, group.show_id), seats_names)
        dispatcher.dispatch(self.db, "ReservationConfirmed", res_event)

        booking_event = BookingEvent(cast(int, booking.id), user_id, cast(int, group.show_id), seats_names, cast(float, booking.total_amount))
        dispatcher.dispatch(self.db, "BookingCreated", booking_event)

        return booking

def get_seat_category_for_show(db: Session, show_id: int, seat_name: str) -> str:
    import math
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        return "Normal"
    total_seats = show.screen.total_seats if show.screen else 220
    cols = 20 if total_seats > 100 else 10
    total_rows_needed = math.ceil(total_seats / cols)
    
    if total_rows_needed == 1:
        normal_rows_count = 1
        executive_rows_count = 0
        premium_rows_count = 0
    elif total_rows_needed == 2:
        normal_rows_count = 1
        executive_rows_count = 1
        premium_rows_count = 0
    else:
        premium_rows_count = max(1, total_rows_needed // 4)
        executive_rows_count = max(1, total_rows_needed // 2)
        normal_rows_count = total_rows_needed - premium_rows_count - executive_rows_count
        if normal_rows_count <= 0:
            normal_rows_count = 1
            executive_rows_count = total_rows_needed - premium_rows_count - normal_rows_count

    row_letters = [chr(65 + i) for i in range(total_rows_needed)]
    executive_start = normal_rows_count
    premium_start = normal_rows_count + executive_rows_count
    
    row_letter = seat_name[0]
    row_idx = row_letters.index(row_letter) if row_letter in row_letters else 0
    
    if row_idx >= premium_start:
        return "Premium"
    elif row_idx >= executive_start:
        return "Executive"
    else:
        return "Normal"
