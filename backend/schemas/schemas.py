from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    class Config:
        from_attributes = True

# --- Movie Schemas ---
class MovieBase(BaseModel):
    title: str
    genre: str
    language: str
    format: str
    release_date: date
    running_days: int
    poster_url: Optional[str] = None
    description: Optional[str] = None
    duration: int
    rating: Optional[float] = None

class MovieCreate(MovieBase):
    pass

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None
    release_date: Optional[date] = None
    running_days: Optional[int] = None
    poster_url: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    rating: Optional[float] = None

class MovieResponse(MovieBase):
    id: int
    class Config:
        from_attributes = True

# --- Seat Schemas ---
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

# --- Theatre & Screens ---
class ScreenBase(BaseModel):
    name: str

class ScreenResponse(ScreenBase):
    id: int
    theatre_id: int
    
    class Config:
        from_attributes = True

class TheatreBase(BaseModel):
    name: str
    location: str

class TheatreResponse(TheatreBase):
    id: int
    screens: List[ScreenResponse] = []
    
    class Config:
        from_attributes = True

# --- Shows ---
class ShowBase(BaseModel):
    movie_id: int
    screen_id: int
    start_time: str
    end_time: str
    date: date
    price_multiplier: float = 1.0

class ShowCreate(ShowBase):
    pass

class ShowResponse(ShowBase):
    id: int
    movie: Optional[MovieResponse] = None
    screen: Optional[ScreenResponse] = None
    
    class Config:
        from_attributes = True

# --- Reviews ---
class ReviewBase(BaseModel):
    rating: int
    comment: str

class ReviewCreate(ReviewBase):
    movie_id: int

class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    movie_id: int
    created_at: datetime
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# --- Bookings ---
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

# Update MovieResponse to include reviews (circular ref handled by deferred eval)
MovieResponse.model_rebuild()
ShowResponse.model_rebuild()

# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str
