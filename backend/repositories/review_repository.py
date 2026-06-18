from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from backend.models.models import Review

class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: int) -> Optional[Review]:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_by_movie_id(self, movie_id: int) -> List[Review]:
        return self.db.query(Review).options(joinedload(Review.user)).filter(Review.movie_id == movie_id).order_by(Review.created_at.desc()).all()

    def get_all(self) -> List[Review]:
        return self.db.query(Review).options(joinedload(Review.user)).all()

    def create(self, review: Review) -> Review:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def delete(self, review: Review) -> None:
        self.db.delete(review)
        self.db.commit()
