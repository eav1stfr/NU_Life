import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    name: str
    role: UserRole
