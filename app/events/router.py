import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.clubs.repository import ClubRepository
from app.common.dependencies import DBSessionDep
from app.common.exceptions import BadRequest, Forbidden, NotFound
from app.events.models import RegistrationStatus
from app.events.repository import EventRepository
from app.events.schemas import EventCreateRequest, EventPublic, EventUpdateRequest
from app.events.service import (
    ClubNotFoundError,
    EventNotFoundError,
    EventService,
    InvalidEventTimesError,
    InvalidStatusTransitionError,
    NotClubOwnerError,
)
from app.users.dependencies import CurrentUser, require_club_admin
from app.users.models import User

router = APIRouter(prefix="/events", tags=["events"])


def get_event_service(db: DBSessionDep) -> EventService:
    return EventService(EventRepository(db), ClubRepository(db))


@router.post("", response_model=EventPublic, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreateRequest,
    db: DBSessionDep,
    admin: Annotated[User, Depends(require_club_admin)],
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventPublic:
    try:
        event = await event_service.create_event(
            admin_user_id=admin.id,
            club_id=payload.club_id,
            title=payload.title,
            description=payload.description,
            location=payload.location,
            start_time=payload.start_time,
            end_time=payload.end_time,
            capacity=payload.capacity,
        )
    except ClubNotFoundError as exc:
        raise NotFound(detail="Club not found") from exc
    except NotClubOwnerError as exc:
        raise Forbidden(detail="You do not administer this club") from exc
    except InvalidEventTimesError as exc:
        raise BadRequest(detail=str(exc)) from exc
    await db.commit()
    return EventPublic.model_validate(event)


@router.get("", response_model=list[EventPublic])
async def list_events(
    event_service: Annotated[EventService, Depends(get_event_service)],
    club_id: uuid.UUID | None = None,
    status_filter: Annotated[RegistrationStatus | None, Query(alias="status")] = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[EventPublic]:
    events = await event_service.list_events(
        club_id=club_id, status=status_filter, start_date=start_date, end_date=end_date
    )
    return [EventPublic.model_validate(event) for event in events]


@router.get("/{event_id}", response_model=EventPublic)
async def get_event(
    event_id: uuid.UUID,
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventPublic:
    try:
        event = await event_service.get_event(event_id)
    except EventNotFoundError as exc:
        raise NotFound(detail="Event not found") from exc
    return EventPublic.model_validate(event)


@router.patch("/{event_id}", response_model=EventPublic)
async def update_event(
    event_id: uuid.UUID,
    payload: EventUpdateRequest,
    db: DBSessionDep,
    admin: CurrentUser,
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventPublic:
    try:
        event = await event_service.update_event(
            admin_user_id=admin.id,
            event_id=event_id,
            title=payload.title,
            description=payload.description,
            location=payload.location,
            start_time=payload.start_time,
            end_time=payload.end_time,
            capacity=payload.capacity,
        )
    except EventNotFoundError as exc:
        raise NotFound(detail="Event not found") from exc
    except NotClubOwnerError as exc:
        raise Forbidden(detail="You do not administer this club") from exc
    except InvalidEventTimesError as exc:
        raise BadRequest(detail=str(exc)) from exc
    await db.commit()
    return EventPublic.model_validate(event)


@router.post("/{event_id}/open", response_model=EventPublic)
async def open_registration(
    event_id: uuid.UUID,
    db: DBSessionDep,
    admin: CurrentUser,
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventPublic:
    try:
        event = await event_service.open_registration(admin_user_id=admin.id, event_id=event_id)
    except EventNotFoundError as exc:
        raise NotFound(detail="Event not found") from exc
    except NotClubOwnerError as exc:
        raise Forbidden(detail="You do not administer this club") from exc
    except InvalidStatusTransitionError as exc:
        raise BadRequest(detail=str(exc)) from exc
    await db.commit()
    return EventPublic.model_validate(event)


@router.post("/{event_id}/close", response_model=EventPublic)
async def close_registration(
    event_id: uuid.UUID,
    db: DBSessionDep,
    admin: CurrentUser,
    event_service: Annotated[EventService, Depends(get_event_service)],
) -> EventPublic:
    try:
        event = await event_service.close_registration(admin_user_id=admin.id, event_id=event_id)
    except EventNotFoundError as exc:
        raise NotFound(detail="Event not found") from exc
    except NotClubOwnerError as exc:
        raise Forbidden(detail="You do not administer this club") from exc
    except InvalidStatusTransitionError as exc:
        raise BadRequest(detail=str(exc)) from exc
    await db.commit()
    return EventPublic.model_validate(event)
