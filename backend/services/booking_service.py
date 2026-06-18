from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, Response
from typing import List
from backend.repositories.booking_repository import BookingRepository
from backend.repositories.theatre_repository import TheatreRepository
from backend.repositories.movie_repository import MovieRepository
from backend.exceptions.booking_exceptions import BookingNotFoundException, ShowNotFoundException, SeatsAlreadyBookedException
from backend.exceptions.base import PermissionDeniedException
from backend.models.models import Booking, BookedSeat, User
from backend.schemas.booking import BookingCreate
from backend.utils.pricing_engine import calculate_dynamic_price
from backend.utils.ticket_generator import generate_ticket_pdf
from backend.utils.email_service import send_booking_confirmation

class BookingService:
    def __init__(self, db: Session):
        self.booking_repo = BookingRepository(db)
        self.theatre_repo = TheatreRepository(db)
        self.movie_repo = MovieRepository(db)
        self.db = db

    async def get_booked_seats(self, show_id: int) -> List[BookedSeat]:
        show = self.theatre_repo.get_show_by_id(show_id)
        if not show:
            raise ShowNotFoundException(show_id)
        return self.booking_repo.get_booked_seats(show_id)

    async def create_booking(self, booking_data: BookingCreate, current_user: User, background_tasks: BackgroundTasks) -> Booking:
        # Verify show exists
        if booking_data.show_id:
            show = self.theatre_repo.get_show_by_id(booking_data.show_id)
            if not show:
                raise ShowNotFoundException(booking_data.show_id)

        # Verify seats are available
        requested_seat_names = [seat.seat_name for seat in booking_data.seats]
        existing = self.booking_repo.get_existing_booked_seats(
            requested_seat_names, booking_data.show_id, booking_data.movie_id
        )
        if existing:
            raise SeatsAlreadyBookedException([e.seat_name for e in existing])

        # Server-side dynamic price recalculation
        calculated_total = 0.0
        for seat in booking_data.seats:
            res = calculate_dynamic_price(self.db, booking_data.show_id, seat.category)
            calculated_total += res["final_price"]

        # Create Booking
        new_booking = Booking(
            user_id=current_user.id,
            movie_id=booking_data.movie_id,
            show_id=booking_data.show_id,
            total_amount=round(calculated_total, 2)
        )
        new_booking = self.booking_repo.create(new_booking)
        self.booking_repo.flush()

        # Create Booked Seats
        for seat in booking_data.seats:
            new_seat = BookedSeat(
                booking_id=new_booking.id,
                movie_id=booking_data.movie_id,
                show_id=booking_data.show_id,
                seat_name=seat.seat_name,
                category=seat.category
            )
            self.booking_repo.add_booked_seat(new_seat)
        self.booking_repo.commit()
        self.booking_repo.refresh(new_booking)

        # Send email confirmation
        try:
            movie = self.movie_repo.get_by_id(new_booking.movie_id)
            show_obj = self.theatre_repo.get_show_by_id(new_booking.show_id) if new_booking.show_id else None
            pdf_bytes = generate_ticket_pdf(new_booking, current_user, movie, show_obj)
            background_tasks.add_task(
                send_booking_confirmation, current_user.email, new_booking.id, movie.title, pdf_bytes
            )
        except Exception as e:
            print(f"Email preparation error: {e}")

        return new_booking

    async def get_user_bookings(self, user_id: int) -> List[Booking]:
        return self.booking_repo.get_user_bookings(user_id)

    async def get_price_calculation(self, show_id: int, category: str) -> dict:
        return calculate_dynamic_price(self.db, show_id, category)

    async def download_ticket(self, booking_id: int, current_user: User) -> Response:
        booking = self.booking_repo.get_by_id_with_relations(booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)

        if booking.user_id != current_user.id and current_user.role != "admin":
            raise PermissionDeniedException("Not authorized to view this ticket")

        pdf_bytes = generate_ticket_pdf(booking, booking.user, booking.movie, booking.show)
        headers = {
            'Content-Disposition': f'attachment; filename="ticket_{booking_id}.pdf"'
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
