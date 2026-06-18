from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.schemas.schemas import BookedSeatResponse, BookingCreate, BookingResponse
from backend.auth.security import get_current_user
from backend.services.booking_service import BookingService
from backend.utils.response import standard_response

router = APIRouter()

def get_booking_service(db: Session = Depends(get_db)) -> BookingService:
    return BookingService(db)

from backend.services.seat_state_service import SeatStateService

def get_seat_state_service(db: Session = Depends(get_db)) -> SeatStateService:
    return SeatStateService(db)

@router.get("/seats/{show_id}")
async def get_booked_seats(
    show_id: int, 
    seat_state_service: SeatStateService = Depends(get_seat_state_service)
):
    statuses = seat_state_service.get_seat_statuses(show_id)
    return standard_response(data=statuses, message="Seat statuses retrieved successfully")

@router.post("/book", status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate, 
    background_tasks: BackgroundTasks, 
    booking_service: BookingService = Depends(get_booking_service), 
    current_user = Depends(get_current_user)
):
    new_booking = await booking_service.create_booking(booking_data, current_user, background_tasks)
    booking_data_res = BookingResponse.model_validate(new_booking)
    return standard_response(data=booking_data_res, message="Booking created successfully")

@router.get("/user/bookings")
async def get_user_bookings(
    booking_service: BookingService = Depends(get_booking_service), 
    current_user = Depends(get_current_user)
):
    bookings = await booking_service.get_user_bookings(current_user.id)
    bookings_data = [BookingResponse.model_validate(b) for b in bookings]
    return standard_response(data=bookings_data, message="User bookings retrieved successfully")

@router.get("/price-calculation")
async def get_price_calculation(
    show_id: int,
    category: str,
    booking_service: BookingService = Depends(get_booking_service)
):
    calc_res = await booking_service.get_price_calculation(show_id, category)
    return standard_response(data=calc_res, message="Price calculation completed")
