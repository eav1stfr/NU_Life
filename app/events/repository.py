import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.models import Event, RegistrationStatus


class EventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        club_id: uuid.UUID,
        title: str,
        description: str,
        location: str,
        start_time: datetime,
        end_time: datetime,
        capacity: int,
    ) -> Event:
        event = Event(
            club_id=club_id,
            title=title,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
        )
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> Event | None:
        return await self._session.get(Event, event_id)

    async def list(
        self,
        *,
        club_id: uuid.UUID | None = None,
        status: RegistrationStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Event]:
        stmt = select(Event)
        if club_id is not None:
            stmt = stmt.where(Event.club_id == club_id)
        if status is not None:
            stmt = stmt.where(Event.registration_status == status)
        if start_date is not None:
            stmt = stmt.where(Event.start_time >= datetime.combine(start_date, time.min, tzinfo=timezone.utc))
        if end_date is not None:
            stmt = stmt.where(Event.start_time <= datetime.combine(end_date, time.max, tzinfo=timezone.utc))
        stmt = stmt.order_by(Event.start_time)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, event: Event) -> Event:
        self._session.add(event)
        await self._session.flush()
        await self._session.refresh(event)
        return event
