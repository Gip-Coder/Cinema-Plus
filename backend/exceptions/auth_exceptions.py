from backend.exceptions.base import UnauthorizedException, BadRequestException

class InvalidCredentialsException(UnauthorizedException):
    def __init__(self, message: str = "Incorrect username or password"):
        super().__init__(detail=message)

class UsernameTakenException(BadRequestException):
    def __init__(self, username: str):
        super().__init__(detail=f"Username '{username}' already taken")

class EmailRegisteredException(BadRequestException):
    def __init__(self, email: str):
        super().__init__(detail=f"Email '{email}' is already registered")

class IncorrectPasswordException(BadRequestException):
    def __init__(self, message: str = "Incorrect old password"):
        super().__init__(detail=message)
