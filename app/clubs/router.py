import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.clubs.repository import ClubRepository
from app.clubs.schemas import ClubCreateRequest, ClubPublic, ClubUpdateRequest
from app.clubs.service import ClubNotFoundError, ClubService, NotClubOwnerError
from app.common.dependencies import DBSessionDep
from app.common.exceptions import Forbidden, NotFound
from app.users.dependencies import CurrentUser, require_club_admin
from app.users.models import User

router = APIRouter(prefix="/clubs", tags=["clubs"])


def get_club_service(db: DBSessionDep) -> ClubService:
    return ClubService(ClubRepository(db))


@router.post("", response_model=ClubPublic, status_code=status.HTTP_201_CREATED)
async def create_club(
    payload: ClubCreateRequest,
    db: DBSessionDep,
    admin: Annotated[User, Depends(require_club_admin)],
    club_service: Annotated[ClubService, Depends(get_club_service)],
) -> ClubPublic:
    club = await club_service.create_club(admin_user_id=admin.id, name=payload.name, description=payload.description)
    await db.commit()
    return ClubPublic.model_validate(club)


@router.get("", response_model=list[ClubPublic])
async def list_clubs(club_service: Annotated[ClubService, Depends(get_club_service)]) -> list[ClubPublic]:
    clubs = await club_service.list_clubs()
    return [ClubPublic.model_validate(club) for club in clubs]


@router.get("/{club_id}", response_model=ClubPublic)
async def get_club(
    club_id: uuid.UUID,
    club_service: Annotated[ClubService, Depends(get_club_service)],
) -> ClubPublic:
    try:
        club = await club_service.get_club(club_id)
    except ClubNotFoundError as exc:
        raise NotFound(detail="Club not found") from exc
    return ClubPublic.model_validate(club)


@router.patch("/{club_id}", response_model=ClubPublic)
async def update_club(
    club_id: uuid.UUID,
    payload: ClubUpdateRequest,
    db: DBSessionDep,
    admin: CurrentUser,
    club_service: Annotated[ClubService, Depends(get_club_service)],
) -> ClubPublic:
    try:
        club = await club_service.update_club(
            admin_user_id=admin.id, club_id=club_id, name=payload.name, description=payload.description
        )
    except ClubNotFoundError as exc:
        raise NotFound(detail="Club not found") from exc
    except NotClubOwnerError as exc:
        raise Forbidden(detail="You do not administer this club") from exc
    await db.commit()
    return ClubPublic.model_validate(club)
