from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.models import Movie
from backend.schemas.schemas import MovieCreate, MovieUpdate, MovieResponse
from backend.auth.security import get_current_admin_user

router = APIRouter()

@router.get("/", response_model=List[MovieResponse])
async def get_movies(db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    return movies

@router.get("/search", response_model=List[MovieResponse])
async def search_movies(
    q: str = None, 
    genre: str = None, 
    language: str = None, 
    db: Session = Depends(get_db)
):
    query = db.query(Movie)
    if q:
        query = query.filter(Movie.title.ilike(f"%{q}%"))
    if genre:
        query = query.filter(Movie.genre == genre)
    if language:
        query = query.filter(Movie.language == language)
    return query.all()

@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@router.post("/upload-poster")
async def upload_poster(file: UploadFile = File(...), current_admin=Depends(get_current_admin_user)):
    import os
    import shutil
    import uuid
    
    # Generate unique filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join("backend", "uploads", "posters", filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"poster_url": f"/static/posters/{filename}"}

@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    new_movie = Movie(**movie.model_dump())
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie

@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(movie_id: int, movie_update: MovieUpdate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    update_data = movie_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_movie, key, value)
        
    db.commit()
    db.refresh(db_movie)
    return db_movie

@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: Session = Depends(get_db), current_admin=Depends(get_current_admin_user)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    db.delete(db_movie)
    db.commit()
    return None
