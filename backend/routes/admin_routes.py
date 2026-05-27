from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.database import get_db
from backend.models.models import Movie, Booking, User, BookedSeat, Show, Theatre, Screen, SeatPricing, PricingRule, MediaAsset, AuditLog
from backend.auth.security import get_current_user, get_current_admin_user
from backend.utils.cache import cache
from backend.utils.media_processor import validate_and_process_image, delete_processed_image
from backend.utils.pricing_engine import validate_seat_hierarchy
from backend.utils.audit_logger import log_action
from typing import List, Dict, Optional
from datetime import date
from backend.schemas.schemas import (
    BookingResponse, TheatreCreate, TheatreUpdate, TheatreResponse,
    ScreenCreate, ScreenUpdate, ScreenResponse,
    SeatPricingCreate, SeatPricingUpdate, SeatPricingResponse,
    PricingRuleCreate, PricingRuleUpdate, PricingRuleResponse,
    MediaAssetResponse, AuditLogResponse
)

router = APIRouter()

# Granular admin authorization dependency
def require_roles(allowed_roles: List[str]):
    async def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not authorized for your role."
            )
        return current_user
    return dependency

# Helper to capture client IP
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

# --- THEATRE MANAGEMENT ---
@router.get("/theatres", response_model=List[TheatreResponse])
async def get_theatres(db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager", "staff"]))):
    # Admins see all theatres
    return db.query(Theatre).all()

@router.post("/theatres", response_model=TheatreResponse)
async def create_theatre(theatre_data: TheatreCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    new_theatre = Theatre(**theatre_data.model_dump())
    db.add(new_theatre)
    db.commit()
    db.refresh(new_theatre)
    
    # Audit log
    log_action(
        db, current_user.id, "theatre", new_theatre.id, "create",
        new_value=theatre_data.model_dump(), ip_address=get_client_ip(request)
    )
    
    # Automatically add default base pricing configurations for the new theatre
    for cat, base_price in [("Normal", 150.0), ("Executive", 220.0), ("Premium", 300.0)]:
        pricing = SeatPricing(
            theatre_id=new_theatre.id,
            seat_category=cat,
            base_price=base_price
        )
        db.add(pricing)
    db.commit()
    
    cache.invalidate("movie:*")
    return new_theatre

@router.put("/theatres/{theatre_id}", response_model=TheatreResponse)
async def update_theatre(theatre_id: int, theatre_data: TheatreUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    theatre = db.query(Theatre).filter(Theatre.id == theatre_id).first()
    if not theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")
        
    old_val = {c.name: getattr(theatre, c.name) for c in theatre.__table__.columns}
    
    update_dict = theatre_data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(theatre, k, v)
        
    db.commit()
    db.refresh(theatre)
    
    # Audit log
    log_action(
        db, current_user.id, "theatre", theatre_id, "update",
        old_value=old_val, new_value=update_dict, ip_address=get_client_ip(request)
    )
    
    cache.invalidate("movie:*")
    return theatre

@router.delete("/theatres/{theatre_id}")
async def delete_theatre(theatre_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin"]))):
    # Soft delete (toggle is_active to False) to preserve integrity of bookings
    theatre = db.query(Theatre).filter(Theatre.id == theatre_id).first()
    if not theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")
        
    old_active = theatre.is_active
    theatre.is_active = False
    db.commit()
    
    # Audit log
    log_action(
        db, current_user.id, "theatre", theatre_id, "soft_delete",
        old_value={"is_active": old_active}, new_value={"is_active": False}, ip_address=get_client_ip(request)
    )
    
    cache.invalidate("movie:*")
    return {"message": "Theatre soft deleted successfully"}

# --- SCREEN MANAGEMENT ---
@router.get("/screens", response_model=List[ScreenResponse])
async def get_screens(db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager", "staff"]))):
    return db.query(Screen).all()

@router.post("/screens", response_model=ScreenResponse)
async def create_screen(screen_data: ScreenCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    new_screen = Screen(**screen_data.model_dump())
    db.add(new_screen)
    db.commit()
    db.refresh(new_screen)
    
    # Audit log
    log_action(
        db, current_user.id, "screen", new_screen.id, "create",
        new_value=screen_data.model_dump(), ip_address=get_client_ip(request)
    )
    return new_screen

@router.put("/screens/{screen_id}", response_model=ScreenResponse)
async def update_screen(screen_id: int, screen_data: ScreenUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    screen = db.query(Screen).filter(Screen.id == screen_id).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    old_val = {c.name: getattr(screen, c.name) for c in screen.__table__.columns}
    
    update_dict = screen_data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(screen, k, v)
        
    db.commit()
    db.refresh(screen)
    
    # Audit log
    log_action(
        db, current_user.id, "screen", screen_id, "update",
        old_value=old_val, new_value=update_dict, ip_address=get_client_ip(request)
    )
    return screen

# --- SEAT PRICING MANAGEMENT ---
@router.get("/pricing", response_model=List[SeatPricingResponse])
async def get_pricings(db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager", "staff"]))):
    return db.query(SeatPricing).all()

@router.put("/pricing/{pricing_id}", response_model=SeatPricingResponse)
async def update_pricing(pricing_id: int, pricing_data: SeatPricingUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    pricing = db.query(SeatPricing).filter(SeatPricing.id == pricing_id).first()
    if not pricing:
        raise HTTPException(status_code=404, detail="Pricing configuration not found")
        
    old_val = {"base_price": pricing.base_price}
    
    # Pre-validation: ascending front-to-back pricing constraint
    # Fetch all pricings for this theatre/screen
    pricings_query = db.query(SeatPricing).filter(
        SeatPricing.theatre_id == pricing.theatre_id,
        SeatPricing.screen_id == pricing.screen_id
    ).all()
    
    # Deep copy query results to simulate the proposed modification
    pricings_sim = []
    for p in pricings_query:
        sim_p = SeatPricing(
            theatre_id=p.theatre_id,
            screen_id=p.screen_id,
            seat_category=p.seat_category,
            base_price=pricing_data.base_price if p.id == pricing_id else p.base_price
        )
        pricings_sim.append(sim_p)
        
    # Run seat ascending hierarchy validation
    # If the user did not specify override header, reject invalid sequences
    admin_override = request.headers.get("X-Admin-Override") == "true"
    valid, msg = validate_seat_hierarchy(pricings_sim, admin_override=admin_override)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
        
    pricing.base_price = pricing_data.base_price
    db.commit()
    db.refresh(pricing)
    
    # Audit log
    log_action(
        db, current_user.id, "pricing", pricing_id, "update",
        old_value=old_val, new_value={"base_price": pricing.base_price}, ip_address=get_client_ip(request)
    )
    return pricing

# --- PRICING RULE ENGINE ---
@router.post("/pricing/rules", response_model=PricingRuleResponse)
async def create_rule(rule_data: PricingRuleCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    # Rule constraints validations
    if rule_data.multiplier <= 0:
        raise HTTPException(status_code=400, detail="Surge multipliers must be positive numbers greater than 0.")
    if rule_data.valid_from and rule_data.valid_to and rule_data.valid_from > rule_data.valid_to:
        raise HTTPException(status_code=400, detail="Invalid date ranges. Start date cannot exceed end date.")
        
    new_rule = PricingRule(**rule_data.model_dump())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    # Audit log
    log_action(
        db, current_user.id, "rule", new_rule.id, "create",
        new_value=rule_data.model_dump(), ip_address=get_client_ip(request)
    )
    return new_rule

@router.put("/pricing/rules/{rule_id}", response_model=PricingRuleResponse)
async def update_rule(rule_id: int, rule_data: PricingRuleUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Pricing rule not found")
        
    old_val = {c.name: getattr(rule, c.name) for c in rule.__table__.columns if c.name != 'created_at'}
    
    update_dict = rule_data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(rule, k, v)
        
    db.commit()
    db.refresh(rule)
    
    # Audit log
    log_action(
        db, current_user.id, "rule", rule_id, "update",
        old_value=old_val, new_value=update_dict, ip_address=get_client_ip(request)
    )
    return rule

# --- MEDIA & MEDIA ASSETS ---
from fastapi import Form
from backend.utils.media_processor import validate_external_image_url
from pydantic import BaseModel

class ExternalMediaRequest(BaseModel):
    image_url: str
    asset_type: str = "original"

@router.post("/media/upload-url", response_model=MediaAssetResponse)
async def upload_media_url(
    request: Request,
    payload: ExternalMediaRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    processed = validate_external_image_url(payload.image_url)
    new_asset = MediaAsset(
        filename=processed["filename"],
        storage_provider="external",
        storage_key=None,
        public_url=processed["public_url"],
        mime_type=processed["mime_type"],
        size_bytes=processed["size_bytes"],
        asset_type=payload.asset_type,
        thumbnail_url=processed["public_url"],
        medium_url=processed["public_url"],
        source_type="external_url",
        original_source_url=payload.image_url
    )
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    
    # Audit log
    log_action(
        db, current_user.id, "media", new_asset.id, "upload_url",
        new_value={"public_url": new_asset.public_url, "source_type": new_asset.source_type},
        ip_address=get_client_ip(request)
    )
    return new_asset

@router.post("/media/upload", response_model=MediaAssetResponse)
async def upload_media(
    request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    asset_type: str = "original",
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    if not file and not image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file upload or external image_url must be provided."
        )

    if file:
        # Option 1: Save local/cloud file
        processed = validate_and_process_image(file, asset_type)
        new_asset = MediaAsset(
            filename=processed["filename"],
            storage_provider="local",
            storage_key=processed["storage_key"],
            public_url=processed["public_url"],
            mime_type=file.content_type or "image/jpeg",
            size_bytes=processed.get("size_bytes", 0),
            asset_type=asset_type,
            thumbnail_url=processed["thumbnail_url"],
            medium_url=processed["medium_url"],
            source_type="upload",
            original_source_url=None
        )
    else:
        # Option 2: Validate and store external URL directly
        processed = validate_external_image_url(image_url)
        new_asset = MediaAsset(
            filename=processed["filename"],
            storage_provider="external",
            storage_key=None,
            public_url=processed["public_url"],
            mime_type=processed["mime_type"],
            size_bytes=processed["size_bytes"],
            asset_type=asset_type,
            thumbnail_url=processed["public_url"],  # store URL directly
            medium_url=processed["public_url"],     # store URL directly
            source_type="external_url",
            original_source_url=image_url
        )

    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    
    # Audit log
    log_action(
        db, current_user.id, "media", new_asset.id, "upload",
        new_value={"public_url": new_asset.public_url, "source_type": new_asset.source_type},
        ip_address=get_client_ip(request)
    )
    return new_asset

@router.delete("/media/{asset_id}")
async def delete_media(asset_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(require_roles(["admin", "theatre_manager"]))):
    asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Media asset not found")
        
    old_val = {"filename": asset.filename, "storage_key": asset.storage_key}
    
    # Safely remove image and thumbnail files from disk
    delete_processed_image(asset.storage_key)
    
    db.delete(asset)
    db.commit()
    
    # Audit log
    log_action(
        db, current_user.id, "media", asset_id, "delete",
        old_value=old_val, ip_address=get_client_ip(request)
    )
    return {"message": "Media asset deleted successfully"}

# --- SYSTEM STATS & BOOKINGS LOGS ---
@router.get("/stats")
async def get_admin_stats(db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    cache_key = "admin:stats"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Run SQL-side aggregate queries directly
    total_movies = db.query(func.count(Movie.id)).scalar() or 0
    total_bookings = db.query(func.count(Booking.id)).filter(Booking.status == 'confirmed').scalar() or 0
    total_revenue = db.query(func.sum(Booking.total_amount)).filter(Booking.status == 'confirmed').scalar() or 0.0
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Most booked movie (SQL aggregation)
    most_booked = db.query(
        Movie.title, func.count(Booking.id).label('booking_count')
    ).join(Booking).filter(Booking.status == 'confirmed').group_by(Movie.id).order_by(desc('booking_count')).first()
    
    most_booked_title = most_booked.title if most_booked else "N/A"
    
    # Occupancy percentage: 220 seats per movie is currently assumed
    total_booked_seats = db.query(func.count(BookedSeat.id)).scalar() or 0
    capacity = total_movies * 220
    occupancy = (total_booked_seats / capacity * 100) if capacity > 0 else 0.0
    
    stats_data = {
        "total_movies": total_movies,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "total_users": total_users,
        "most_booked_movie": most_booked_title,
        "occupancy_percentage": round(occupancy, 1)
    }
    
    cache.set(cache_key, stats_data, ttl=30)
    return stats_data

@router.get("/revenue-chart")
async def get_revenue_chart(db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    cache_key = "admin:revenue_chart"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    results = db.query(
        func.date(Booking.booking_date).label('date'),
        func.sum(Booking.total_amount).label('revenue')
    ).filter(Booking.status == 'confirmed').group_by(func.date(Booking.booking_date)).order_by(func.date(Booking.booking_date)).all()
    
    dates = [str(r.date) for r in results]
    revenues = [float(r.revenue) for r in results]
    chart_data = {"dates": dates, "revenues": revenues}
    
    cache.set(cache_key, chart_data, ttl=30)
    return chart_data

@router.get("/booking-trends")
async def get_booking_trends(db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    cache_key = "admin:booking_trends"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    results = db.query(
        func.date(Booking.booking_date).label('date'),
        func.count(Booking.id).label('count')
    ).filter(Booking.status == 'confirmed').group_by(func.date(Booking.booking_date)).order_by(func.date(Booking.booking_date)).all()
    
    dates = [str(r.date) for r in results]
    counts = [r.count for r in results]
    trends_data = {"dates": dates, "counts": counts}
    
    cache.set(cache_key, trends_data, ttl=30)
    return trends_data

@router.get("/bookings", response_model=List[BookingResponse])
async def get_all_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db), 
    current_admin=Depends(get_current_admin_user)
):
    from sqlalchemy.orm import joinedload, selectinload
    # Eager load relationships to prevent N+1 query problem and apply pagination
    return db.query(Booking).options(
        joinedload(Booking.movie),
        joinedload(Booking.show).joinedload(Show.screen),
        selectinload(Booking.booked_seats)
    ).order_by(Booking.booking_date.desc()).offset(skip).limit(limit).all()

@router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    booking.status = "cancelled"
    db.query(BookedSeat).filter(BookedSeat.booking_id == booking_id).delete()
    db.commit()
    
    cache.invalidate("admin:*")
    return {"message": "Booking cancelled"}

@router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    db.delete(booking)
    db.commit()
    
    cache.invalidate("admin:*")
    return {"message": "Booking deleted"}
