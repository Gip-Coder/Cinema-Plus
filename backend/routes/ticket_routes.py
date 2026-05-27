from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.models import Booking
from backend.auth.security import get_current_user
from backend.utils.ticket_generator import generate_ticket_pdf

router = APIRouter()

@router.get("/ticket/{booking_id}/pdf")
async def download_ticket(booking_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
        
    pdf_bytes = generate_ticket_pdf(booking, booking.user, booking.movie, booking.show)
    
    headers = {
        'Content-Disposition': f'attachment; filename="ticket_{booking_id}.pdf"'
    }
    
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
