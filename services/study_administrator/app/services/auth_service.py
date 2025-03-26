import os
from datetime import datetime, timedelta, timezone
import jwt

from fastapi import status
from fastapi.exceptions import HTTPException

from app.repositories.auth_repository import AuthRepository
from app.models.user import User

COOKIE_EXPIRY_DAYS = 7


class AuthService:
    def __init__(self, auth_repository: AuthRepository):
        self.auth_repository = auth_repository
        self.cookie_key = os.getenv("COOKIE_KEY")
        self.cookie_expiry_days = COOKIE_EXPIRY_DAYS
        self.encode_algorithm = os.getenv("ENCODE_ALGORITHM")

    def add_roles_to_user(self, user: User) -> User:
        user_roles = self.auth_repository.get_user_roles(user.user_id)
        user.roles = user_roles
        return user

    def get_custom_token(self, user: User | None):
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user was provided or found in firebase authentication.",
            )
        user.expiration_date = (
            datetime.now(timezone.utc) + timedelta(days=self.cookie_expiry_days)
        ).timestamp()
        user = self.add_roles_to_user(user)
        return jwt.encode(
            user.model_dump(),
            self.cookie_key,
            algorithm=self.encode_algorithm,
        )

    def decode_custom_token(self, token: str) -> User:
        return User(
            **jwt.decode(token, self.cookie_key, algorithms=[self.encode_algorithm])
        )


def get_auth_service():
    auth_repository = AuthRepository()
    return AuthService(auth_repository)
