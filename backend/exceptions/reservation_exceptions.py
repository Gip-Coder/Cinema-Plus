from backend.exceptions.base import NotFoundException, BadRequestException, ConflictException

class ReservationNotFoundException(NotFoundException):
    def __init__(self, group_id: int):
        super().__init__(detail=f"Reservation group with ID {group_id} was not found.")

class ReservationExpiredException(BadRequestException):
    def __init__(self, group_id: int):
        super().__init__(detail=f"Reservation group with ID {group_id} has expired.")

class ReservationAlreadyConvertedException(BadRequestException):
    def __init__(self, group_id: int):
        super().__init__(detail=f"Reservation group with ID {group_id} has already been confirmed.")

class SeatsAlreadyReservedException(ConflictException):
    def __init__(self, seat_names: list[str]):
        super().__init__(detail=f"Seats already reserved by another transaction: {', '.join(seat_names)}")
