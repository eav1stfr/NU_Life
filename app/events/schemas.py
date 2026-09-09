import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.events.models import RegistrationStatus


class EventCreateRequest(BaseModel):
    club_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    location: str = Field(min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(gt=0)

    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, end_time: datetime, info) -> datetime:
        start_time = info.data.get("start_time")
        if start_time is not None and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class EventUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, min_length=1, max_length=255)
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: int | None = Field(default=None, gt=0)


class EventPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    club_id: uuid.UUID
    title: str
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    capacity: int
    registration_status: RegistrationStatus
