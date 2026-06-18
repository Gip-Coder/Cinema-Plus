from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.models import Movie

class MovieRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, movie_id: int) -> Optional[Movie]:
        return self.db.query(Movie).filter(Movie.id == movie_id, Movie.is_deleted == False).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Movie]:
        return self.db.query(Movie).filter(Movie.is_deleted == False).offset(skip).limit(limit).all()

    def search(self, q: Optional[str] = None, genre: Optional[str] = None, language: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Movie]:
        query = self.db.query(Movie).filter(Movie.is_deleted == False)
        if q:
            query = query.filter(Movie.title.ilike(f"%{q}%"))
        if genre:
            query = query.filter(Movie.genre == genre)
        if language:
            query = query.filter(Movie.language == language)
        return query.offset(skip).limit(limit).all()

    def create(self, movie: Movie) -> Movie:
        self.db.add(movie)
        self.db.commit()
        self.db.refresh(movie)
        return movie

    def save(self, movie: Movie) -> Movie:
        self.db.add(movie)
        self.db.commit()
        self.db.refresh(movie)
        return movie
