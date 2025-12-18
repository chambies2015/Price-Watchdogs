from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class SnapshotBase(BaseModel):
    service_id: UUID
    raw_html_hash: str
    normalized_content_hash: str
    normalized_content: str


class SnapshotCreate(SnapshotBase):
    pass


class SnapshotResponse(SnapshotBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

