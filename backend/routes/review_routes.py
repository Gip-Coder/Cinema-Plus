from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models.models import Review, Movie
from backend.schemas.schemas import ReviewCreate, ReviewResponse
from backend.auth.security import get_current_user, get_current_admin_user

router = APIRouter()

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Verify movie exists
    movie = db.query(Movie).filter(Movie.id == review.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    db_review = Review(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.get("/movie/{movie_id}", response_model=List[ReviewResponse])
async def get_movie_reviews(movie_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.movie_id == movie_id).order_by(Review.created_at.desc()).all()

@router.delete("/{review_id}")
async def delete_review(review_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin_user)):
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(db_review)
    db.commit()
    return {"message": "Review deleted"}

@router.get("/all", response_model=List[ReviewResponse])
async def get_all_reviews(db: Session = Depends(get_db), current_admin = Depends(get_current_admin_user)):
    return db.query(Review).all()
