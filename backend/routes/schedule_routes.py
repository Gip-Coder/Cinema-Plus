from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.schemas.schemas import TheatreBase, TheatreResponse, ScreenBase, ScreenResponse, ShowCreate, ShowResponse, ScreenCreate
from backend.auth.security import get_current_admin_user
from backend.services.theatre_service import TheatreService
from backend.utils.response import standard_response

router = APIRouter()

def get_theatre_service(db: Session = Depends(get_db)) -> TheatreService:
    return TheatreService(db)

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

# --- Theatres ---
@router.post("/theatres")
async def create_theatre(
    request: Request,
    theatre: TheatreBase, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_admin = Depends(get_current_admin_user)
):
    ip = get_client_ip(request)
    db_theatre = await theatre_service.create_theatre(theatre, current_admin, ip)
    theatre_data = TheatreResponse.model_validate(db_theatre)
    return standard_response(data=theatre_data, message="Theatre created successfully")

@router.get("/theatres")
async def get_theatres(theatre_service: TheatreService = Depends(get_theatre_service)):
    theatres = await theatre_service.get_theatres()
    theatres_data = [TheatreResponse.model_validate(t) for t in theatres]
    return standard_response(data=theatres_data, message="Theatres retrieved successfully")

# --- Screens ---
@router.post("/screens")
async def create_screen(
    request: Request,
    screen: ScreenBase, 
    theatre_id: int, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_admin = Depends(get_current_admin_user)
):
    ip = get_client_ip(request)
    screen_create = ScreenCreate(**screen.model_dump(), theatre_id=theatre_id)
    db_screen = await theatre_service.create_screen(screen_create, current_admin, ip)
    screen_data = ScreenResponse.model_validate(db_screen)
    return standard_response(data=screen_data, message="Screen created successfully")

@router.get("/screens")
async def get_screens(theatre_service: TheatreService = Depends(get_theatre_service)):
    screens = await theatre_service.get_screens()
    screens_data = [ScreenResponse.model_validate(s) for s in screens]
    return standard_response(data=screens_data, message="Screens retrieved successfully")

# --- Shows ---
@router.post("/shows")
async def create_show(
    request: Request,
    show: ShowCreate, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_admin = Depends(get_current_admin_user)
):
    ip = get_client_ip(request)
    db_show = await theatre_service.create_show(show, current_admin, ip)
    show_data = ShowResponse.model_validate(db_show)
    return standard_response(data=show_data, message="Show created successfully")

@router.get("/shows/{movie_id}")
async def get_shows_by_movie(
    movie_id: int, 
    theatre_service: TheatreService = Depends(get_theatre_service)
):
    shows = await theatre_service.get_shows_by_movie(movie_id)
    shows_data = [ShowResponse.model_validate(s) for s in shows]
    return standard_response(data=shows_data, message="Shows for movie retrieved successfully")

@router.get("/shows/all/")
async def get_all_shows(theatre_service: TheatreService = Depends(get_theatre_service)):
    shows = await theatre_service.get_all_shows()
    shows_data = [ShowResponse.model_validate(s) for s in shows]
    return standard_response(data=shows_data, message="All shows retrieved successfully")

@router.get("/shows/show/{show_id}")
async def get_show(
    show_id: int, 
    theatre_service: TheatreService = Depends(get_theatre_service)
):
    show = await theatre_service.get_show(show_id)
    show_data = ShowResponse.model_validate(show)
    return standard_response(data=show_data, message="Show retrieved successfully")

@router.delete("/shows/{show_id}")
async def delete_show(
    request: Request,
    show_id: int, 
    theatre_service: TheatreService = Depends(get_theatre_service), 
    current_admin = Depends(get_current_admin_user)
):
    ip = get_client_ip(request)
    await theatre_service.delete_show(show_id, current_admin, ip)
    return standard_response(message="Show deleted successfully")
