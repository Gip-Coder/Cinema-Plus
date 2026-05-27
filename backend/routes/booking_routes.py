from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.models import BookedSeat, Booking, Movie, Show
from backend.schemas.schemas import SeatBase, BookedSeatResponse, BookingCreate, BookingResponse
from backend.auth.security import get_current_user
from backend.utils.ticket_generator import generate_ticket_pdf
from backend.utils.email_service import send_booking_confirmation

router = APIRouter()

@router.get("/seats/{show_id}", response_model=List[BookedSeatResponse])
async def get_booked_seats(show_id: int, db: Session = Depends(get_db)):
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
        
    booked_seats = db.query(BookedSeat).filter(BookedSeat.show_id == show_id).all()
    return booked_seats

@router.post("/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking_data: BookingCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Verify show exists
    if booking_data.show_id:
        show = db.query(Show).filter(Show.id == booking_data.show_id).first()
        if not show:
            raise HTTPException(status_code=404, detail="Show not found")
            
    # Verify seats are available
    requested_seat_names = [seat.seat_name for seat in booking_data.seats]
    
    query = db.query(BookedSeat).filter(BookedSeat.seat_name.in_(requested_seat_names))
    if booking_data.show_id:
        query = query.filter(BookedSeat.show_id == booking_data.show_id)
    else:
        query = query.filter(BookedSeat.movie_id == booking_data.movie_id)
        
    existing_bookings = query.all()
    
    if existing_bookings:
        booked_names = [b.seat_name for b in existing_bookings]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Seats already booked: {', '.join(booked_names)}"
        )
        
    # Create Booking
    new_booking = Booking(
        user_id=current_user.id,
        movie_id=booking_data.movie_id,
        show_id=booking_data.show_id,
        total_amount=booking_data.total_amount
    )
    db.add(new_booking)
    db.flush() # flush to get booking.id
    
    # Create BookedSeats
    for seat in booking_data.seats:
        new_seat = BookedSeat(
            booking_id=new_booking.id,
            movie_id=booking_data.movie_id,
            show_id=booking_data.show_id,
            seat_name=seat.seat_name,
            category=seat.category
        )
        db.add(new_seat)
        
    db.commit()
    db.refresh(new_booking)

    # Send confirmation email in background
    try:
        movie = db.query(Movie).filter(Movie.id == new_booking.movie_id).first()
        show = db.query(Show).filter(Show.id == new_booking.show_id).first() if new_booking.show_id else None
        pdf_bytes = generate_ticket_pdf(new_booking, current_user, movie, show)
        background_tasks.add_task(send_booking_confirmation, current_user.email, new_booking.id, movie.title, pdf_bytes)
    except Exception as e:
        print(f"Email preparation error: {e}")

    return new_booking

@router.get("/user/bookings", response_model=List[BookingResponse])
async def get_user_bookings(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).order_by(Booking.booking_date.desc()).all()
    return bookings
