from sqlalchemy.orm import Session
from backend.models.reservation import ReservationGroup
from datetime import datetime, timezone
from sqlalchemy import func

def get_reservation_metrics(db: Session) -> dict:
    """
    Computes real-time reservation metrics and conversion rates.
    """
    now = datetime.now(timezone.utc)
    
    # Active Reservations (unexpired and not converted/cancelled)
    active_count = db.query(func.count(ReservationGroup.id)).filter(
        ReservationGroup.status == "active",
        ReservationGroup.expires_at > now
    ).scalar() or 0
    
    # Expired Reservations (either explicitly marked or active but past expiry time)
    expired_count = db.query(func.count(ReservationGroup.id)).filter(
        (ReservationGroup.status == "expired") | 
        ((ReservationGroup.status == "active") & (ReservationGroup.expires_at <= now))
    ).scalar() or 0
    
    # Converted Reservations (successfully turned into permanent bookings)
    converted_count = db.query(func.count(ReservationGroup.id)).filter(
        ReservationGroup.status == "converted"
    ).scalar() or 0
    
    # Cancelled Reservations
    cancelled_count = db.query(func.count(ReservationGroup.id)).filter(
        ReservationGroup.status == "cancelled"
    ).scalar() or 0
    
    total = converted_count + expired_count + cancelled_count
    conversion_rate = (converted_count / total * 100) if total > 0 else 0.0
    
    return {
        "active_reservations": active_count,
        "expired_reservations": expired_count,
        "converted_reservations": converted_count,
        "cancelled_reservations": cancelled_count,
        "conversion_rate": round(conversion_rate, 2)
    }
