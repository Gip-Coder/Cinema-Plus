from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date
from backend.database import get_db
from backend.models.models import Movie, Booking, User, BookedSeat
from backend.auth.security import get_current_admin_user

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    total_movies = db.query(func.count(Movie.id)).scalar()
    total_bookings = db.query(func.count(Booking.id)).filter(Booking.status == 'confirmed').scalar()
    total_revenue = db.query(func.sum(Booking.total_amount)).filter(Booking.status == 'confirmed').scalar() or 0.0
    total_users = db.query(func.count(User.id)).scalar()
    
    # Most booked movie
    most_booked = db.query(
        Movie.title, func.count(Booking.id).label('booking_count')
    ).join(Booking).filter(Booking.status == 'confirmed').group_by(Movie.id).order_by(desc('booking_count')).first()
    
    most_booked_title = most_booked.title if most_booked else "N/A"
    
    # Occupancy percentage: 220 seats per movie is currently assumed
    total_booked_seats = db.query(func.count(BookedSeat.id)).scalar()
    capacity = total_movies * 220
    occupancy = (total_booked_seats / capacity * 100) if capacity > 0 else 0.0
    
    return {
        "total_movies": total_movies,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "total_users": total_users,
        "most_booked_movie": most_booked_title,
        "occupancy_percentage": round(occupancy, 1)
    }

@router.get("/revenue-chart")
async def get_revenue_chart(db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    results = db.query(
        func.date(Booking.booking_date).label('date'),
        func.sum(Booking.total_amount).label('revenue')
    ).filter(Booking.status == 'confirmed').group_by(func.date(Booking.booking_date)).order_by(func.date(Booking.booking_date)).all()
    
    dates = [str(r.date) for r in results]
    revenues = [float(r.revenue) for r in results]
    return {"dates": dates, "revenues": revenues}

@router.get("/booking-trends")
async def get_booking_trends(db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    results = db.query(
        func.date(Booking.booking_date).label('date'),
        func.count(Booking.id).label('count')
    ).filter(Booking.status == 'confirmed').group_by(func.date(Booking.booking_date)).order_by(func.date(Booking.booking_date)).all()
    
    dates = [str(r.date) for r in results]
    counts = [r.count for r in results]
    return {"dates": dates, "counts": counts}

from typing import List
from backend.schemas.schemas import BookingResponse

@router.get("/bookings", response_model=List[BookingResponse])
async def get_all_bookings(db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    return db.query(Booking).order_by(Booking.booking_date.desc()).all()

@router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    from fastapi import HTTPException
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    booking.status = "cancelled"
    # Remove booked seats to make them available again
    db.query(BookedSeat).filter(BookedSeat.booking_id == booking_id).delete()
    db.commit()
    return {"message": "Booking cancelled"}

@router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    from fastapi import HTTPException
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted"}
