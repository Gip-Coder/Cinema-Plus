from sqlalchemy.orm import Session
from backend.repositories.movie_repository import MovieRepository
from backend.exceptions.movie_exceptions import MovieNotFoundException
from backend.models.models import Movie, User
from backend.schemas.movie import MovieCreate, MovieUpdate
from backend.utils.cache import cache
from datetime import datetime, timezone

class MovieService:
    def __init__(self, db: Session):
        self.movie_repo = MovieRepository(db)
        self.db = db

    async def get_movie(self, movie_id: int) -> Movie:
        movie = self.movie_repo.get_by_id(movie_id)
        if not movie:
            raise MovieNotFoundException(movie_id)
        return movie

    async def get_movies(self, skip: int = 0, limit: int = 100) -> list[Movie]:
        return self.movie_repo.get_all(skip, limit)

    async def search_movies(self, q: str = None, genre: str = None, language: str = None, skip: int = 0, limit: int = 100) -> list[Movie]:
        return self.movie_repo.search(q, genre, language, skip, limit)

    async def create_movie(self, movie_data: MovieCreate, current_user: User, client_ip: str) -> Movie:
        movie_dict = movie_data.model_dump()
        if not movie_dict.get("poster_url") or not movie_dict["poster_url"].strip():
            movie_dict["poster_url"] = "/uploads/defaults/no-poster.png"
            movie_dict["poster_source_type"] = "upload"
            
        new_movie = Movie(**movie_dict)
        new_movie.poster_uploaded_at = datetime.now(timezone.utc)
        new_movie.is_deleted = False
        
        movie = self.movie_repo.create(new_movie)
        
        # Log action
        from backend.utils.audit_logger import log_action
        log_action(
            self.db, current_user.id, "movie", movie.id, "create",
            new_value=movie_data.model_dump(), ip_address=client_ip
        )
        
        # Invalidate cache
        cache.invalidate("movie:*")
        cache.invalidate("admin:*")
        return movie

    async def update_movie(self, movie_id: int, movie_update: MovieUpdate, current_user: User, client_ip: str) -> Movie:
        movie = self.movie_repo.get_by_id(movie_id)
        if not movie:
            raise MovieNotFoundException(movie_id)
            
        old_val = {c.name: getattr(movie, c.name) for c in movie.__table__.columns if c.name != 'poster_uploaded_at'}
        update_data = movie_update.model_dump(exclude_unset=True)
        
        if "poster_url" in update_data:
            if not update_data["poster_url"] or not update_data["poster_url"].strip():
                update_data["poster_url"] = "/uploads/defaults/no-poster.png"
                update_data["poster_source_type"] = "upload"
            movie.poster_uploaded_at = datetime.now(timezone.utc)
            
        for key, value in update_data.items():
            setattr(movie, key, value)
            
        movie = self.movie_repo.save(movie)
        
        # Log action
        from backend.utils.audit_logger import log_action
        log_action(
            self.db, current_user.id, "movie", movie_id, "update",
            old_value=old_val, new_value=update_data, ip_address=client_ip
        )
        
        # Invalidate cache
        cache.invalidate("movie:*")
        cache.invalidate("admin:*")
        return movie

    async def delete_movie(self, movie_id: int, current_user: User, client_ip: str) -> None:
        movie = self.movie_repo.get_by_id(movie_id)
        if not movie:
            raise MovieNotFoundException(movie_id)
            
        old_val = {"is_deleted": movie.is_deleted, "deleted_at": movie.deleted_at}
        
        movie.is_deleted = True
        movie.deleted_at = datetime.now(timezone.utc)
        self.movie_repo.save(movie)
        
        # Log action
        from backend.utils.audit_logger import log_action
        log_action(
            self.db, current_user.id, "movie", movie_id, "soft_delete",
            old_value=old_val, new_value={"is_deleted": True, "deleted_at": movie.deleted_at.isoformat() + "Z"},
            ip_address=client_ip
        )
        
        cache.invalidate("movie:*")
        cache.invalidate("admin:*")
