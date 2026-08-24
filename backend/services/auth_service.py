from sqlalchemy.orm import Session
from datetime import timedelta
from backend.repositories.user_repository import UserRepository
from backend.exceptions.auth_exceptions import InvalidCredentialsException, UsernameTakenException, EmailRegisteredException, IncorrectPasswordException
from backend.auth.security import verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models.models import User
from backend.schemas.auth import UserCreate
from backend.utils.cache import cache

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    async def register(self, user_data: UserCreate) -> User:
        if self.user_repo.get_by_username(user_data.username):
            raise UsernameTakenException(user_data.username)
        if self.user_repo.get_by_email(user_data.email):
            raise EmailRegisteredException(user_data.email)
            
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role="customer"
        )
        user = self.user_repo.create(new_user)
        cache.invalidate("admin:*")
        return user

    async def login(self, username: str, password: str) -> dict:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    async def update_profile(self, current_user: User, username: str | None = None, email: str | None = None) -> User:
        if username and username != current_user.username:
            if self.user_repo.get_by_username(username):
                raise UsernameTakenException(username)
            current_user.username = username
        if email:
            current_user.email = email
        return self.user_repo.save(current_user)

    async def change_password(self, current_user: User, old_password: str, new_password: str) -> User:
        if not verify_password(old_password, current_user.hashed_password):
            raise IncorrectPasswordException()
        current_user.hashed_password = get_password_hash(new_password)
        return self.user_repo.save(current_user)
