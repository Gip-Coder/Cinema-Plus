from backend.exceptions.base import NotFoundException, BadRequestException, ConflictException

class BookingNotFoundException(NotFoundException):
    def __init__(self, booking_id: int):
        super().__init__(detail=f"Booking with ID {booking_id} was not found.")

class ShowNotFoundException(NotFoundException):
    def __init__(self, show_id: int):
        super().__init__(detail=f"Show with ID {show_id} was not found.")

class SeatsAlreadyBookedException(ConflictException):
    def __init__(self, seat_names: list[str]):
        super().__init__(detail=f"Seats already booked: {', '.join(seat_names)}")

class InvalidBookingRequestException(BadRequestException):
    def __init__(self, message: str):
        super().__init__(detail=message)
