from sqlalchemy.orm import Session
from typing import List
from backend.repositories.review_repository import ReviewRepository
from backend.repositories.movie_repository import MovieRepository
from backend.models.models import Review, User
from backend.schemas.review import ReviewCreate
from backend.exceptions.movie_exceptions import MovieNotFoundException
from backend.exceptions.base import NotFoundException, PermissionDeniedException
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

    async def delete_review(self, review_id: int, current_user: User) -> None:
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise NotFoundException("Review not found")
        if current_user.role not in ["admin", "superadmin"] and review.user_id != current_user.id:
            raise PermissionDeniedException("You cannot delete this review")
        self.review_repo.delete(review)
        cache.invalidate("reviews:*")

    async def update_review(self, review_id: int, review_data: ReviewCreate, current_user: User) -> Review:
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise NotFoundException("Review not found")
        if review.user_id != current_user.id:
            raise PermissionDeniedException("You cannot edit this review")
        
        review.rating = review_data.rating
        review.comment = review_data.comment
        self.review_repo.db.commit()
        self.review_repo.db.refresh(review)
        cache.invalidate("reviews:*")
        return review

