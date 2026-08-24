from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserResponse(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    """Request body for updating user profile details."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    """Request body for changing the user's password.
    Credentials must NEVER be passed as URL query parameters.
    """
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long.")
        return v
