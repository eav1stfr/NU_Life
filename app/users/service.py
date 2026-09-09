from app.users.models import User, UserRole
from app.users.repository import UserRepository
from app.users.security import create_access_token, hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self._users = user_repository

    async def register(self, *, email: str, password: str, name: str, role: UserRole) -> User:
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise EmailAlreadyRegisteredError(email)
        return await self._users.create(email=email, password_hash=hash_password(password), name=name, role=role)

    async def authenticate(self, *, email: str, password: str) -> User:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        return create_access_token(user.id)
