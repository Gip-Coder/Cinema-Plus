from sqlalchemy.orm import Session
from typing import List
from backend.repositories.review_repository import ReviewRepository
from backend.repositories.movie_repository import MovieRepository
from backend.models.models import Review, User
from backend.schemas.review import ReviewCreate
from backend.exceptions.movie_exceptions import MovieNotFoundException
from backend.exceptions.base import NotFoundException
from backend.utils.cache import cache

class ReviewService:
    def __init__(self, db: Session):
        self.review_repo = ReviewRepository(db)
        self.movie_repo = MovieRepository(db)

    async def create_review(self, review_data: ReviewCreate, current_user: User) -> Review:
        movie = self.movie_repo.get_by_id(review_data.movie_id)
        if not movie:
            raise MovieNotFoundException(review_data.movie_id)
            
        new_review = Review(**review_data.model_dump(), user_id=current_user.id)
        review = self.review_repo.create(new_review)
        cache.invalidate("reviews:*")
        return review

    async def get_movie_reviews(self, movie_id: int) -> List[Review]:
        return self.review_repo.get_by_movie_id(movie_id)

    async def get_all_reviews(self) -> List[Review]:
        return self.review_repo.get_all()

    async def delete_review(self, review_id: int) -> None:
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise NotFoundException("Review not found")
        self.review_repo.delete(review)
        cache.invalidate("reviews:*")
