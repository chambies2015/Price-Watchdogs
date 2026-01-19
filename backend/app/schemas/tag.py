from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7)


class TagResponse(TagBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
