from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.change_event import ChangeType
from app.schemas.snapshot import SnapshotResponse


class ChangeEventResponse(BaseModel):
    id: UUID
    service_id: UUID
    old_snapshot_id: UUID | None
    new_snapshot_id: UUID
    change_type: ChangeType
    summary: str
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ChangeEventDetailResponse(BaseModel):
    id: UUID
    service_id: UUID
    old_snapshot_id: UUID | None
    new_snapshot_id: UUID
    change_type: ChangeType
    summary: str
    confidence_score: float
    created_at: datetime
    old_snapshot: Optional[SnapshotResponse]
    new_snapshot: SnapshotResponse

    class Config:
        from_attributes = True

