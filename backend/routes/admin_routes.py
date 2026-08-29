from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.auth.security import get_current_user, get_current_admin_user
from backend.exceptions.base import PermissionDeniedException
from backend.services.theatre_service import TheatreService
from backend.services.admin_service import AdminService
from backend.utils.response import standard_response
from backend.schemas.schemas import (
    BookingResponse, TheatreCreate, TheatreUpdate, TheatreResponse,
    ScreenCreate, ScreenUpdate, ScreenResponse,
    SeatPricingCreate, SeatPricingUpdate, SeatPricingResponse,
    PricingRuleCreate, PricingRuleUpdate, PricingRuleResponse,
    AuditLogResponse
)

router = APIRouter()

# Granular admin authorization dependency
def require_roles(allowed_roles: List[str]):
    async def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException("Operation not authorized for your role.")
        return current_user
    return dependency

# Helper to capture client IP
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def get_theatre_service(db: Session = Depends(get_db)) -> TheatreService:
    return TheatreService(db)

def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)

# --- THEATRE MANAGEMENT ---
@router.get("/theatres")
async def get_theatres(
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager", "staff"]))
):
    theatres = await theatre_service.get_theatres()
    theatres_data = [TheatreResponse.model_validate(t) for t in theatres]
    return standard_response(data=theatres_data, message="Theatres retrieved successfully")

@router.post("/theatres")
async def create_theatre(
    request: Request,
    theatre_data: TheatreCreate, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    ip = get_client_ip(request)
    db_theatre = await theatre_service.create_theatre(theatre_data, current_user, ip)
    theatre_res = TheatreResponse.model_validate(db_theatre)
    return standard_response(data=theatre_res, message="Theatre created successfully")

@router.put("/theatres/{theatre_id}")
async def update_theatre(
    theatre_id: int, 
    theatre_data: TheatreUpdate, 
    request: Request, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    ip = get_client_ip(request)
    db_theatre = await theatre_service.update_theatre(theatre_id, theatre_data, current_user, ip)
    theatre_res = TheatreResponse.model_validate(db_theatre)
    return standard_response(data=theatre_res, message="Theatre updated successfully")

@router.delete("/theatres/{theatre_id}")
async def delete_theatre(
    theatre_id: int, 
    request: Request, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin"]))
):
    ip = get_client_ip(request)
    await theatre_service.delete_theatre(theatre_id, current_user, ip)
    return standard_response(message="Theatre deleted successfully")

# --- SCREEN MANAGEMENT ---
@router.get("/screens")
async def get_screens(
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager", "staff"]))
):
    screens = await theatre_service.get_screens()
    screens_data = [ScreenResponse.model_validate(s) for s in screens]
    return standard_response(data=screens_data, message="Screens retrieved successfully")

@router.post("/screens")
async def create_screen(
    screen_data: ScreenCreate, 
    request: Request, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    ip = get_client_ip(request)
    db_screen = await theatre_service.create_screen(screen_data, current_user, ip)
    screen_res = ScreenResponse.model_validate(db_screen)
    return standard_response(data=screen_res, message="Screen created successfully")

@router.put("/screens/{screen_id}")
async def update_screen(
    screen_id: int, 
    screen_data: ScreenUpdate, 
    request: Request, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    ip = get_client_ip(request)
    db_screen = await theatre_service.update_screen(screen_id, screen_data, current_user, ip)
    screen_res = ScreenResponse.model_validate(db_screen)
    return standard_response(data=screen_res, message="Screen updated successfully")

# --- SEAT PRICING MANAGEMENT ---
@router.get("/pricing")
async def get_pricings(
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager", "staff"]))
):
    pricings = await theatre_service.get_pricings()
    pricings_data = [SeatPricingResponse.model_validate(p) for p in pricings]
    return standard_response(data=pricings_data, message="Pricings retrieved successfully")

@router.put("/pricing/{pricing_id}")
async def update_pricing(
    pricing_id: int, 
    pricing_data: SeatPricingUpdate, 
    request: Request, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    ip = get_client_ip(request)
    admin_override = request.headers.get("X-Admin-Override") == "true"
    db_pricing = await theatre_service.update_pricing(pricing_id, pricing_data, current_user, admin_override, ip)
    pricing_res = SeatPricingResponse.model_validate(db_pricing)
    return standard_response(data=pricing_res, message="Pricing updated successfully")

# --- PRICING RULE ENGINE ---
@router.post("/pricing/rules")
async def create_rule(
    rule_data: PricingRuleCreate, 
    request: Request, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    ip = get_client_ip(request)
    db_rule = await theatre_service.create_rule(rule_data, current_user, ip)
    rule_res = PricingRuleResponse.model_validate(db_rule)
    return standard_response(data=rule_res, message="Pricing rule created successfully")

@router.put("/pricing/rules/{rule_id}")
async def update_rule(
    rule_id: int, 
    rule_data: PricingRuleUpdate, 
    request: Request, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_user=Depends(require_roles(["admin", "theatre_manager"]))
):
    ip = get_client_ip(request)
    db_rule = await theatre_service.update_rule(rule_id, rule_data, current_user, ip)
    rule_res = PricingRuleResponse.model_validate(db_rule)
    return standard_response(data=rule_res, message="Pricing rule updated successfully")

# --- SYSTEM STATS & BOOKINGS LOGS ---
# NOTE: the standalone Media Library endpoints (POST /media/upload,
# POST /media/upload-url, DELETE /media/{asset_id}) were removed here.
# They only ever backed the standalone Admin Media Library UI
# (src/app/admin/media/page.tsx, removed), which could not even list its
# own assets. Movie poster uploads do NOT depend on these routes — they
# go through POST /api/movies/upload-poster (backend/routes/movie_routes.py),
# which calls MediaService.upload_local_media / register_external_media
# directly and is untouched by this change.
@router.get("/stats")
async def get_admin_stats(
    admin_service: AdminService = Depends(get_admin_service), 
    current_admin=Depends(get_current_admin_user)
):
    stats = await admin_service.get_admin_stats()
    return standard_response(data=stats, message="Stats retrieved successfully")

@router.get("/revenue-chart")
async def get_revenue_chart(
    admin_service: AdminService = Depends(get_admin_service), 
    current_admin=Depends(get_current_admin_user)
):
    chart = await admin_service.get_revenue_chart()
    return standard_response(data=chart, message="Revenue chart retrieved successfully")

@router.get("/booking-trends")
async def get_booking_trends(
    admin_service: AdminService = Depends(get_admin_service), 
    current_admin=Depends(get_current_admin_user)
):
    trends = await admin_service.get_booking_trends()
    return standard_response(data=trends, message="Booking trends retrieved successfully")

@router.get("/bookings")
async def get_all_bookings(
    skip: int = 0,
    limit: int = 100,
    admin_service: AdminService = Depends(get_admin_service), 
    current_admin=Depends(get_current_admin_user)
):
    bookings = await admin_service.get_all_bookings(skip, limit)
    bookings_data = [BookingResponse.model_validate(b) for b in bookings]
    return standard_response(data=bookings_data, message="All bookings retrieved successfully")

@router.put("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    current_admin=Depends(get_current_admin_user)
):
    await admin_service.cancel_booking(booking_id)
    return standard_response(message="Booking cancelled successfully")

@router.delete("/bookings/{booking_id}")
async def delete_booking(
    booking_id: int, 
    admin_service: AdminService = Depends(get_admin_service), 
    current_admin=Depends(get_current_admin_user)
):
    await admin_service.delete_booking(booking_id)
    return standard_response(message="Booking deleted successfully")

@router.get("/audit")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    admin_service: AdminService = Depends(get_admin_service),
    current_admin=Depends(require_roles(["super_admin", "admin"]))
):
    logs = await admin_service.get_audit_logs(skip, limit)
    logs_data = [AuditLogResponse.model_validate(l) for l in logs]
    return standard_response(data=logs_data, message="Audit logs retrieved successfully")

@router.get("/health")
async def get_system_health(
    admin_service: AdminService = Depends(get_admin_service),
    current_admin=Depends(require_roles(["super_admin", "admin"]))
):
    health = await admin_service.get_system_health()
    return standard_response(data=health, message="System health retrieved successfully")
