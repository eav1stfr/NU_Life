import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clubs.models import Club


class ClubRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, *, name: str, description: str, admin_user_id: uuid.UUID) -> Club:
        club = Club(name=name, description=description, admin_user_id=admin_user_id)
        self._session.add(club)
        await self._session.flush()
        await self._session.refresh(club)
        return club

    async def get_by_id(self, club_id: uuid.UUID) -> Club | None:
        return await self._session.get(Club, club_id)

    async def list_all(self) -> list[Club]:
        result = await self._session.execute(select(Club).order_by(Club.name))
        return list(result.scalars().all())

    async def update(self, club: Club) -> Club:
        self._session.add(club)
        await self._session.flush()
        await self._session.refresh(club)
        return club
