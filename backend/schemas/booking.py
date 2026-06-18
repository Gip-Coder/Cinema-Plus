from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.schemas.movie import MovieResponse
from backend.schemas.theatre import ShowResponse

class SeatBase(BaseModel):
    seat_name: str
    category: str
    show_id: Optional[int] = None

class BookedSeatBase(SeatBase):
    pass

class BookedSeatCreate(BookedSeatBase):
    pass

class BookedSeatResponse(BookedSeatBase):
    id: int
    booking_id: int
    
    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    movie_id: int
    show_id: Optional[int] = None
    total_amount: float

class BookingCreate(BookingBase):
    seats: List[BookedSeatCreate]

class BookingResponse(BookingBase):
    id: int
    user_id: int
    booking_date: datetime
    status: str
    booked_seats: List[BookedSeatResponse]
    movie: MovieResponse
    show: Optional[ShowResponse] = None
    
    class Config:
        from_attributes = True
