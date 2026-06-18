from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.schemas.auth import UserResponse

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
