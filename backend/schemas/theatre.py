from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from backend.schemas.movie import MovieResponse

class ScreenBase(BaseModel):
    name: str
    screen_type: str = "Standard"
    total_seats: int = 220
    seat_layout_json: Optional[str] = None
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
