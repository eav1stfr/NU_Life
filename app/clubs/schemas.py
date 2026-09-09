import uuid

from pydantic import BaseModel, ConfigDict, Field


class ClubCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""


class ClubUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ClubPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    admin_user_id: uuid.UUID
