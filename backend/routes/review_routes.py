from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.schemas.schemas import ReviewCreate, ReviewResponse
from backend.auth.security import get_current_user, get_current_admin_user
from backend.services.review_service import ReviewService
from backend.utils.response import standard_response
from backend.utils.cache import cache

router = APIRouter()

def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate, 
    review_service: ReviewService = Depends(get_review_service), 
    current_user = Depends(get_current_user)
):
    db_review = await review_service.create_review(review, current_user)
    review_data = ReviewResponse.model_validate(db_review)
    return standard_response(data=review_data, message="Review created successfully")

@router.get("/movie/{movie_id}")
async def get_movie_reviews(
    movie_id: int, 
    review_service: ReviewService = Depends(get_review_service)
):
    cache_key = f"reviews:movie:{movie_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return standard_response(data=cached, message="Reviews retrieved from cache")

    reviews = await review_service.get_movie_reviews(movie_id)
    reviews_data = [ReviewResponse.model_validate(r) for r in reviews]
    cache.set(cache_key, reviews_data, ttl=120)
    return standard_response(data=reviews_data, message="Reviews retrieved successfully")

@router.delete("/{review_id}")
async def delete_review(
    review_id: int, 
    review_service: ReviewService = Depends(get_review_service), 
    current_admin = Depends(get_current_admin_user)
):
    await review_service.delete_review(review_id)
    return standard_response(message="Review deleted successfully")

@router.get("/all")
async def get_all_reviews(
    review_service: ReviewService = Depends(get_review_service), 
    current_admin = Depends(get_current_admin_user)
):
    cache_key = "reviews:all"
    cached = cache.get(cache_key)
    if cached is not None:
        return standard_response(data=cached, message="All reviews retrieved from cache")

    reviews = await review_service.get_all_reviews()
    reviews_data = [ReviewResponse.model_validate(r) for r in reviews]
    cache.set(cache_key, reviews_data, ttl=120)
    return standard_response(data=reviews_data, message="All reviews retrieved successfully")
