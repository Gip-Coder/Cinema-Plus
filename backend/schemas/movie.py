from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date

class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    genre: str = Field(..., min_length=1, max_length=100)
    language: str = Field(..., min_length=1, max_length=100)
    format: str = Field(..., min_length=1, max_length=50)
    release_date: date
    running_days: int = Field(..., gt=0)
    poster_url: Optional[str] = None
    poster_source_type: Optional[str] = Field("upload", max_length=50)
    description: Optional[str] = None
    duration: int = Field(..., gt=0)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    status: str = Field("Now Showing", description="Status: Now Showing, Coming Soon, or Archived")

    @field_validator("poster_url")
    @classmethod
    def validate_poster_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        v_stripped = v.strip()
        if not v_stripped:
            return None
        if v_stripped.startswith("/uploads/"):
            return v_stripped
        if v_stripped.startswith("http://") or v_stripped.startswith("https://"):
            return v_stripped
        raise ValueError("Poster URL must start with http://, https://, or local path /uploads/")

class MovieCreate(MovieBase):
    pass

class MovieUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    genre: Optional[str] = Field(None, min_length=1, max_length=100)
    language: Optional[str] = Field(None, min_length=1, max_length=100)
    format: Optional[str] = Field(None, min_length=1, max_length=50)
    release_date: Optional[date] = None
    running_days: Optional[int] = Field(None, gt=0)
    poster_url: Optional[str] = None
    poster_source_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    duration: Optional[int] = Field(None, gt=0)
    rating: Optional[float] = Field(None, ge=0.0, le=10.0)
    status: Optional[str] = None

    @field_validator("poster_url")
    @classmethod
    def validate_poster_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        v_stripped = v.strip()
        if not v_stripped:
            return None
        if v_stripped.startswith("/uploads/"):
            return v_stripped
        if v_stripped.startswith("http://") or v_stripped.startswith("https://"):
            return v_stripped
        raise ValueError("Poster URL must start with http://, https://, or local path /uploads/")

class MovieResponse(MovieBase):
    id: int
    poster_uploaded_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
