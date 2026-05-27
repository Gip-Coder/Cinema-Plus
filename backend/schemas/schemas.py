from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
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
    screen_type: str = "Standard" # IMAX, 3D, Standard, Dolby Atmos
    total_seats: int = 220
    seat_layout_json: Optional[str] = None # JSON string format
    is_active: bool = True

class ScreenCreate(ScreenBase):
    theatre_id: int

class ScreenUpdate(BaseModel):
    name: Optional[str] = None
    screen_type: Optional[str] = None
    total_seats: Optional[int] = None
    seat_layout_json: Optional[str] = None
    is_active: Optional[bool] = None

class ScreenResponse(ScreenBase):
    id: int
    theatre_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TheatreBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    timezone: str = "UTC"
    contact_info: Optional[str] = None
    description: Optional[str] = None
    banner_image_url: Optional[str] = None
    is_active: bool = True

class TheatreCreate(TheatreBase):
    pass

class TheatreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    timezone: Optional[str] = None
    contact_info: Optional[str] = None
    description: Optional[str] = None
    banner_image_url: Optional[str] = None
    is_active: Optional[bool] = None

class TheatreResponse(TheatreBase):
    id: int
    screens: List[ScreenResponse] = []
    created_at: datetime
    updated_at: datetime
    
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

# --- Dynamic Seat Pricing ---
class SeatPricingBase(BaseModel):
    theatre_id: int
    screen_id: Optional[int] = None
    seat_category: str # Premium, Executive, Normal
    base_price: float = Field(..., gt=0)
    currency: str = "INR"

class SeatPricingCreate(SeatPricingBase):
    pass

class SeatPricingUpdate(BaseModel):
    base_price: float = Field(..., gt=0)

class SeatPricingResponse(SeatPricingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# --- Pricing Rules ---
class PricingRuleBase(BaseModel):
    name: str
    rule_type: str # weekend, holiday, event, surge, time_based
    multiplier: float = Field(..., gt=0)
    priority: int = 0
    stackable: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: bool = True
    theatre_id: Optional[int] = None
    screen_id: Optional[int] = None

class PricingRuleCreate(PricingRuleBase):
    pass

class PricingRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    multiplier: Optional[float] = Field(None, gt=0)
    priority: Optional[int] = None
    stackable: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None

class PricingRuleResponse(PricingRuleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Media Asset ---
class MediaAssetResponse(BaseModel):
    id: int
    filename: str
    storage_provider: str
    storage_key: Optional[str] = None
    public_url: Optional[str] = None
    mime_type: str
    size_bytes: int
    asset_type: str
    thumbnail_url: Optional[str] = None
    medium_url: Optional[str] = None
    source_type: str
    original_source_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Audit Log ---
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    entity_type: str
    entity_id: int
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

# --- Auth Login ---
class LoginRequest(BaseModel):
    username: str
    password: str

# Rebuild models for deferred evaluation
MovieResponse.model_rebuild()
ShowResponse.model_rebuild()
