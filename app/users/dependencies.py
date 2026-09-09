import uuid
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.dependencies import DBSessionDep
from app.common.exceptions import Forbidden, Unauthorized
from app.users.models import User, UserRole
from app.users.repository import UserRepository
from app.users.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DBSessionDep,
) -> User:
    credentials_error = Unauthorized(
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_error

    try:
        user_id: uuid.UUID = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise credentials_error from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    async def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise Forbidden(detail="Not authorized")
        return user

    return _check


require_club_admin = require_role(UserRole.CLUB_ADMIN)
