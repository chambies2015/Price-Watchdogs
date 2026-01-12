from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

