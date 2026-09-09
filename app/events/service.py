import uuid
from datetime import date, datetime

from app.clubs.repository import ClubRepository
from app.events.models import Event, RegistrationStatus
from app.events.repository import EventRepository


class EventNotFoundError(Exception):
    pass


class ClubNotFoundError(Exception):
    pass


class NotClubOwnerError(Exception):
    pass


class InvalidEventTimesError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass


class EventService:
    def __init__(self, event_repository: EventRepository, club_repository: ClubRepository):
        self._events = event_repository
        self._clubs = club_repository

    async def _get_owned_club(self, *, admin_user_id: uuid.UUID, club_id: uuid.UUID):
        club = await self._clubs.get_by_id(club_id)
        if club is None:
            raise ClubNotFoundError(club_id)
        if club.admin_user_id != admin_user_id:
            raise NotClubOwnerError(club_id)
        return club

    async def _get_owned_event(self, *, admin_user_id: uuid.UUID, event_id: uuid.UUID) -> Event:
        event = await self.get_event(event_id)
        await self._get_owned_club(admin_user_id=admin_user_id, club_id=event.club_id)
        return event

    async def create_event(
        self,
        *,
        admin_user_id: uuid.UUID,
        club_id: uuid.UUID,
        title: str,
        description: str,
        location: str,
        start_time: datetime,
        end_time: datetime,
        capacity: int,
    ) -> Event:
        await self._get_owned_club(admin_user_id=admin_user_id, club_id=club_id)
        if end_time <= start_time:
            raise InvalidEventTimesError("end_time must be after start_time")

        return await self._events.create(
            club_id=club_id,
            title=title,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
        )

    async def get_event(self, event_id: uuid.UUID) -> Event:
        event = await self._events.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError(event_id)
        return event

    async def list_events(
        self,
        *,
        club_id: uuid.UUID | None = None,
        status: RegistrationStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Event]:
        return await self._events.list(club_id=club_id, status=status, start_date=start_date, end_date=end_date)

    async def update_event(
        self,
        *,
        admin_user_id: uuid.UUID,
        event_id: uuid.UUID,
        title: str | None,
        description: str | None,
        location: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        capacity: int | None,
    ) -> Event:
        event = await self._get_owned_event(admin_user_id=admin_user_id, event_id=event_id)

        new_start = start_time if start_time is not None else event.start_time
        new_end = end_time if end_time is not None else event.end_time
        if new_end <= new_start:
            raise InvalidEventTimesError("end_time must be after start_time")

        if title is not None:
            event.title = title
        if description is not None:
            event.description = description
        if location is not None:
            event.location = location
        event.start_time = new_start
        event.end_time = new_end
        if capacity is not None:
            event.capacity = capacity

        return await self._events.update(event)

    async def open_registration(self, *, admin_user_id: uuid.UUID, event_id: uuid.UUID) -> Event:
        event = await self._get_owned_event(admin_user_id=admin_user_id, event_id=event_id)
        if event.registration_status != RegistrationStatus.NOT_OPEN:
            raise InvalidStatusTransitionError("Registration can only be opened from not_open")
        event.registration_status = RegistrationStatus.OPEN
        return await self._events.update(event)

    async def close_registration(self, *, admin_user_id: uuid.UUID, event_id: uuid.UUID) -> Event:
        event = await self._get_owned_event(admin_user_id=admin_user_id, event_id=event_id)
        if event.registration_status != RegistrationStatus.OPEN:
            raise InvalidStatusTransitionError("Registration can only be closed from open")
        event.registration_status = RegistrationStatus.CLOSED
        return await self._events.update(event)
