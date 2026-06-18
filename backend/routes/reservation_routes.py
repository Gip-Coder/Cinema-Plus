from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.schemas import ReservationCreate, ReservationGroupResponse, BookingResponse
from backend.auth.security import get_current_user
from backend.services.reservation_service import ReservationService
from backend.services.seat_state_service import SeatStateService
from backend.utils.response import standard_response
from backend.models.reservation import ReservationGroup
from backend.exceptions.reservation_exceptions import ReservationNotFoundException
from backend.exceptions.base import PermissionDeniedException

router = APIRouter()

def get_reservation_service(db: Session = Depends(get_db)) -> ReservationService:
    return ReservationService(db)

def get_seat_state_service(db: Session = Depends(get_db)) -> SeatStateService:
    return SeatStateService(db)

@router.post("/reservations", status_code=status.HTTP_201_CREATED)
async def create_reservation(
    payload: ReservationCreate,
    reservation_service: ReservationService = Depends(get_reservation_service),
    current_user = Depends(get_current_user)
):
    group = reservation_service.create_reservation_group(
        show_id=payload.show_id,
        seat_names=payload.seats,
        user_id=current_user.id
    )
    group_data = ReservationGroupResponse.model_validate(group)
    return standard_response(data=group_data, message="Seats temporarily reserved")

@router.get("/reservations/{group_id}")
async def get_reservation_details(
    group_id: int,
    reservation_service: ReservationService = Depends(get_reservation_service),
    current_user = Depends(get_current_user)
):
    group = reservation_service.db.query(ReservationGroup).filter(
        ReservationGroup.id == group_id
    ).first()
    if not group:
        raise ReservationNotFoundException(group_id)
        
    if group.user_id != current_user.id and current_user.role != "admin":
        raise PermissionDeniedException("Not authorized to view this reservation.")
        
    group_data = ReservationGroupResponse.model_validate(group)
    return standard_response(data=group_data, message="Reservation details retrieved")

@router.delete("/reservations/{group_id}")
async def cancel_reservation(
    group_id: int,
    reservation_service: ReservationService = Depends(get_reservation_service),
    current_user = Depends(get_current_user)
):
    reservation_service.cancel_reservation(group_id, current_user.id)
    return standard_response(message="Reservation cancelled and seats released")

@router.post("/reservations/{group_id}/confirm")
async def confirm_reservation(
    group_id: int,
    reservation_service: ReservationService = Depends(get_reservation_service),
    current_user = Depends(get_current_user)
):
    booking = reservation_service.confirm_reservation(group_id, current_user.id)
    booking_data = BookingResponse.model_validate(booking)
    return standard_response(data=booking_data, message="Booking confirmed successfully")

@router.get("/shows/{show_id}/seat-status")
async def get_show_seat_status(
    show_id: int,
    seat_state_service: SeatStateService = Depends(get_seat_state_service)
):
    statuses = seat_state_service.get_seat_statuses(show_id)
    return standard_response(data=statuses, message="Seat statuses retrieved")

from sqlalchemy import func
from backend.exceptions.booking_exceptions import ShowNotFoundException

@router.get("/admin/shows/{show_id}/stats")
async def get_show_stats(
    show_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise PermissionDeniedException("Not authorized to access show stats.")
        
    from backend.models.models import Show, BookedSeat, Booking
    from backend.models.reservation import SeatReservation, ReservationGroup
    from datetime import datetime
    
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise ShowNotFoundException(show_id)
        
    capacity = show.screen.total_seats if show.screen else 220
    
    # Booked count
    booked_count = (
        db.query(func.count(BookedSeat.id))
        .join(Booking, BookedSeat.booking_id == Booking.id)
        .filter(BookedSeat.show_id == show_id)
        .filter(Booking.status != "cancelled")
        .scalar() or 0
    )
    
    # Active, unexpired reserved count
    now = datetime.utcnow()
    reserved_count = (
        db.query(func.count(SeatReservation.id))
        .join(ReservationGroup, SeatReservation.reservation_group_id == ReservationGroup.id)
        .filter(SeatReservation.show_id == show_id)
        .filter(ReservationGroup.status == "active")
        .filter(ReservationGroup.expires_at > now)
        .filter(SeatReservation.status == "active")
        .scalar() or 0
    )
    
    # Converted, expired, cancelled counts for conversion rate
    converted_count = db.query(func.count(ReservationGroup.id)).filter(
        ReservationGroup.show_id == show_id,
        ReservationGroup.status == "converted"
    ).scalar() or 0
    
    expired_count = db.query(func.count(ReservationGroup.id)).filter(
        ReservationGroup.show_id == show_id,
        (ReservationGroup.status == "expired") | 
        ((ReservationGroup.status == "active") & (ReservationGroup.expires_at <= now))
    ).scalar() or 0
    
    cancelled_count = db.query(func.count(ReservationGroup.id)).filter(
        ReservationGroup.show_id == show_id,
        ReservationGroup.status == "cancelled"
    ).scalar() or 0
    
    total_res = converted_count + expired_count + cancelled_count
    conversion_rate = (converted_count / total_res * 100) if total_res > 0 else 0.0
    
    return standard_response(data={
        "capacity": capacity,
        "booked_count": booked_count,
        "reserved_count": reserved_count,
        "occupancy_rate": round((booked_count / capacity) * 100, 2) if capacity > 0 else 0.0,
        "reservation_rate": round((reserved_count / capacity) * 100, 2) if capacity > 0 else 0.0,
        "conversion_rate": round(conversion_rate, 2),
        "reservation_metrics": {
            "converted": converted_count,
            "expired": expired_count,
            "cancelled": cancelled_count
        }
    }, message="Show statistics retrieved")
