from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.models import User
from backend.schemas.auth import (
    UserCreate,
    UserResponse,
    LoginRequest,
    Token,
    ChangePasswordRequest,
    ProfileUpdateRequest,
)
from backend.auth.security import get_current_user
from backend.services.auth_service import AuthService
from backend.utils.response import standard_response
from backend.utils.rate_limiter import enforce_login_rate_limit, enforce_register_rate_limit

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    user_data = UserResponse.model_validate(current_user)
    return standard_response(data=user_data, message="Current user retrieved")


@router.put("/profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    """Update username and/or email. Both fields are optional."""
    updated_user = await auth_service.update_profile(
        current_user, payload.username, payload.email
    )
    user_data = UserResponse.model_validate(updated_user)
    return standard_response(data=user_data, message="Profile updated successfully")


@router.put("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user),
):
    """Change the authenticated user's password.

    Credentials are passed in the request BODY — never in URL query parameters,
    which would expose them in server logs and browser history.
    """
    await auth_service.change_password(
        current_user, payload.old_password, payload.new_password
    )
    return standard_response(message="Password updated successfully")


@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(enforce_register_rate_limit)])
async def register(
    user: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    new_user = await auth_service.register(user)
    user_data = UserResponse.model_validate(new_user)
    return standard_response(data=user_data, message="Registration successful")


@router.post("/login", dependencies=[Depends(enforce_login_rate_limit)])
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    token_dict = await auth_service.login(login_data.username, login_data.password)
    return standard_response(data=token_dict, message="Login successful")
