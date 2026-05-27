from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models.models import Movie
from backend.schemas.schemas import MovieCreate, MovieUpdate, MovieResponse
from backend.auth.security import get_current_admin_user
from backend.utils.cache import cache

router = APIRouter()

@router.get("/", response_model=List[MovieResponse])
async def get_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cache_key = f"movie:list:{skip}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
        
    movies = db.query(Movie).offset(skip).limit(limit).all()
    cache.set(cache_key, movies, ttl=300)
    return movies

@router.get("/search", response_model=List[MovieResponse])
async def search_movies(
    q: str = None, 
    genre: str = None, 
    language: str = None, 
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    cache_key = f"movie:search:{q}:{genre}:{language}:{skip}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    query = db.query(Movie)
    if q:
        query = query.filter(Movie.title.ilike(f"%{q}%"))
    if genre:
        query = query.filter(Movie.genre == genre)
    if language:
        query = query.filter(Movie.language == language)
        
    movies = query.offset(skip).limit(limit).all()
    cache.set(cache_key, movies, ttl=300)
    return movies

@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, db: Session = Depends(get_db)):
    cache_key = f"movie:detail:{movie_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    cache.set(cache_key, movie, ttl=180)
    return movie

@router.post("/upload-poster")
async def upload_poster(
    request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    current_admin=Depends(get_current_admin_user)
):
    import os
    import uuid
    from PIL import Image
    from backend.utils.media_processor import validate_external_image_url
    
    # Support JSON payload
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            image_url = body.get("image_url") or body.get("poster_url")
        except Exception:
            pass

    if not file and not image_url:
        raise HTTPException(
            status_code=400,
            detail="Either file or image_url must be provided."
        )

    if file:
        # 1. MIME Validation
        allowed_mimes = {"image/jpeg", "image/png", "image/webp"}
        if file.content_type not in allowed_mimes:
            raise HTTPException(status_code=400, detail="Invalid image type. Only JPEG, PNG, and WEBP allowed.")
            
        # 2. Max size check (2MB)
        content = await file.read()
        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds the 2MB limit.")
            
        # Reset read pointer
        file.file.seek(0)
        
        # 3. Broken image validation (Pillow header scan)
        try:
            img = Image.open(file.file)
            img.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Corrupted or invalid image headers.")
            
        # Reset read pointer and save securely
        file.file.seek(0)
        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Create target directory
        os.makedirs(os.path.join("backend", "uploads", "posters"), exist_ok=True)
        os.makedirs(os.path.join("uploads", "posters"), exist_ok=True)
        
        file_path = os.path.join("backend", "uploads", "posters", filename)
        file_path_root = os.path.join("uploads", "posters", filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        with open(file_path_root, "wb") as buffer:
            buffer.write(content)
            
        url = f"/uploads/posters/{filename}"
    else:
        # Validate external URL
        processed = validate_external_image_url(image_url)
        url = processed["public_url"]
        
    return {"poster_url": url}

@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    # Add temporary logging for debugging movie creation flow
    print(f"[DEBUG MOVIE CREATION] Payload received: {movie.model_dump()}")
    print(f"[DEBUG MOVIE CREATION] Poster URL: {movie.poster_url}")
    
    movie_dict = movie.model_dump()
    if not movie_dict.get("poster_url") or not movie_dict["poster_url"].strip():
        movie_dict["poster_url"] = "/uploads/defaults/no-poster.png"
        
    new_movie = Movie(**movie_dict)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    
    print(f"[DEBUG MOVIE CREATION] DB insert success. Inserted Movie ID: {new_movie.id}")
    
    # Invalidate movie cache
    cache.invalidate("movie:*")
    return new_movie

@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(movie_id: int, movie_update: MovieUpdate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    update_data = movie_update.model_dump(exclude_unset=True)
    if "poster_url" in update_data and (not update_data["poster_url"] or not update_data["poster_url"].strip()):
        update_data["poster_url"] = "/uploads/defaults/no-poster.png"
        
    for key, value in update_data.items():
        setattr(db_movie, key, value)
        
    db.commit()
    db.refresh(db_movie)
    
    # Invalidate movie cache
    cache.invalidate("movie:*")
    return db_movie

@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    db.delete(db_movie)
    db.commit()
    
    # Invalidate movie cache
    cache.invalidate("movie:*")
    return None
