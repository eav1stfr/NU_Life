from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.common.dependencies import DBSessionDep
from app.common.exceptions import Duplicate, Unauthorized
from app.users.dependencies import CurrentUser
from app.users.repository import UserRepository
from app.users.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.users.service import AuthService, EmailAlreadyRegisteredError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: DBSessionDep) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: DBSessionDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user = await auth_service.register(
            email=payload.email, password=payload.password, name=payload.name, role=payload.role
        )
    except EmailAlreadyRegisteredError as exc:
        raise Duplicate(detail="Email already registered") from exc
    await db.commit()
    token = auth_service.issue_token(user)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user = await auth_service.authenticate(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise Unauthorized(detail="Invalid email or password") from exc
    token = auth_service.issue_token(user)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
async def me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)
