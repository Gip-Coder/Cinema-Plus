from backend.exceptions.base import NotFoundException, BadRequestException

class MovieNotFoundException(NotFoundException):
    def __init__(self, movie_id: int):
        super().__init__(detail=f"Movie with ID {movie_id} was not found.")

class InvalidMovieDataException(BadRequestException):
    def __init__(self, message: str):
        super().__init__(detail=message)
