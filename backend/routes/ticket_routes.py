from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth.security import get_current_user
from backend.services.booking_service import BookingService

router = APIRouter()

def get_booking_service(db: Session = Depends(get_db)) -> BookingService:
    return BookingService(db)

@router.get("/ticket/{booking_id}/pdf")
async def download_ticket(
    booking_id: int, 
    booking_service: BookingService = Depends(get_booking_service), 
    current_user = Depends(get_current_user)
):
    return await booking_service.download_ticket(booking_id, current_user)
