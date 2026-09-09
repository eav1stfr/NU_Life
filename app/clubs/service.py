import uuid

from app.clubs.models import Club
from app.clubs.repository import ClubRepository


class ClubNotFoundError(Exception):
    pass


class NotClubOwnerError(Exception):
    pass


class ClubService:
    def __init__(self, club_repository: ClubRepository):
        self._clubs = club_repository

    async def create_club(self, *, admin_user_id: uuid.UUID, name: str, description: str) -> Club:
        return await self._clubs.create(name=name, description=description, admin_user_id=admin_user_id)

    async def get_club(self, club_id: uuid.UUID) -> Club:
        club = await self._clubs.get_by_id(club_id)
        if club is None:
            raise ClubNotFoundError(club_id)
        return club

    async def list_clubs(self) -> list[Club]:
        return await self._clubs.list_all()

    async def update_club(
        self,
        *,
        admin_user_id: uuid.UUID,
        club_id: uuid.UUID,
        name: str | None,
        description: str | None,
    ) -> Club:
        club = await self.get_club(club_id)
        if club.admin_user_id != admin_user_id:
            raise NotClubOwnerError(club_id)

        if name is not None:
            club.name = name
        if description is not None:
            club.description = description

        return await self._clubs.update(club)
