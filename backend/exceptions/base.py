from fastapi import status

class CinemaPlusException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class NotFoundException(CinemaPlusException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationException(CinemaPlusException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422), detail=detail)

class BadRequestException(CinemaPlusException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class PermissionDeniedException(CinemaPlusException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class UnauthorizedException(CinemaPlusException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class ConflictException(CinemaPlusException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class RateLimitExceededException(CinemaPlusException):
    def __init__(self, detail: str = "Too many requests. Please try again later."):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
