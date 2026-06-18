from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.schemas.schemas import MovieCreate, MovieUpdate, MovieResponse
from backend.auth.security import get_current_admin_user
from backend.services.movie_service import MovieService
from backend.services.media_service import MediaService
from backend.utils.response import standard_response
from backend.utils.cache import cache

router = APIRouter()

def get_movie_service(db: Session = Depends(get_db)) -> MovieService:
    return MovieService(db)

def get_media_service(db: Session = Depends(get_db)) -> MediaService:
    return MediaService(db)

# Helper to capture client IP
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.get("/")
async def get_movies(
    skip: int = 0, 
    limit: int = 100, 
    movie_service: MovieService = Depends(get_movie_service)
):
    cache_key = f"movie:list:{skip}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return standard_response(data=cached, message="Movies retrieved from cache")
        
    movies = await movie_service.get_movies(skip, limit)
    movies_data = [MovieResponse.model_validate(m) for m in movies]
    cache.set(cache_key, movies_data, ttl=300)
    return standard_response(data=movies_data, message="Movies retrieved successfully")

@router.get("/search")
async def search_movies(
    q: Optional[str] = None, 
    genre: Optional[str] = None, 
    language: Optional[str] = None, 
    skip: int = 0,
    limit: int = 100,
    movie_service: MovieService = Depends(get_movie_service)
):
    cache_key = f"movie:search:{q}:{genre}:{language}:{skip}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return standard_response(data=cached, message="Movies retrieved from cache")

    movies = await movie_service.search_movies(q, genre, language, skip, limit)
    movies_data = [MovieResponse.model_validate(m) for m in movies]
    cache.set(cache_key, movies_data, ttl=300)
    return standard_response(data=movies_data, message="Movies retrieved successfully")

@router.get("/{movie_id}")
async def get_movie(
    movie_id: int, 
    movie_service: MovieService = Depends(get_movie_service)
):
    cache_key = f"movie:detail:{movie_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return standard_response(data=cached, message="Movie detail retrieved from cache")

    movie = await movie_service.get_movie(movie_id)
    movie_data = MovieResponse.model_validate(movie)
    cache.set(cache_key, movie_data, ttl=180)
    return standard_response(data=movie_data, message="Movie detail retrieved successfully")

@router.post("/upload-poster")
async def upload_poster(
    request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    media_service: MediaService = Depends(get_media_service),
    current_admin = Depends(get_current_admin_user)
):
    # Support JSON payload (for URL-based uploads from frontend JSON request)
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            image_url = body.get("image_url") or body.get("poster_url")
        except Exception:
            pass

    from fastapi import HTTPException
    if not file and not image_url:
        raise HTTPException(
            status_code=400,
            detail="Either file or image_url must be provided."
        )

    client_ip = get_client_ip(request)
    if file:
        asset = await media_service.upload_local_media(file, "poster", current_admin, client_ip)
    else:
        # Cast image_url to str (already verified truthiness)
        asset = await media_service.register_external_media(str(image_url), "poster", current_admin, client_ip)
        
    return standard_response(data={"poster_url": asset.public_url}, message="Poster uploaded successfully")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_movie(
    request: Request,
    movie: MovieCreate, 
    movie_service: MovieService = Depends(get_movie_service), 
    current_admin = Depends(get_current_admin_user)
):
    client_ip = get_client_ip(request)
    db_movie = await movie_service.create_movie(movie, current_admin, client_ip)
    movie_data = MovieResponse.model_validate(db_movie)
    return standard_response(data=movie_data, message="Movie created successfully")

@router.put("/{movie_id}")
async def update_movie(
    movie_id: int, 
    request: Request, 
    movie_update: MovieUpdate, 
    movie_service: MovieService = Depends(get_movie_service), 
    current_admin = Depends(get_current_admin_user)
):
    client_ip = get_client_ip(request)
    db_movie = await movie_service.update_movie(movie_id, movie_update, current_admin, client_ip)
    movie_data = MovieResponse.model_validate(db_movie)
    return standard_response(data=movie_data, message="Movie updated successfully")

@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int, 
    request: Request, 
    movie_service: MovieService = Depends(get_movie_service), 
    current_admin = Depends(get_current_admin_user)
):
    client_ip = get_client_ip(request)
    await movie_service.delete_movie(movie_id, current_admin, client_ip)
    return None
