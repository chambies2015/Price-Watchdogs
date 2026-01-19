from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.change_event import ChangeType
from app.models.service import CheckFrequency
from app.schemas.tag import TagResponse


class ChangeEventSummary(BaseModel):
    id: UUID
    change_type: ChangeType
    summary: str
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceSummary(BaseModel):
    id: UUID
    name: str
    url: str
    is_active: bool
    check_frequency: CheckFrequency
    last_checked_at: Optional[datetime]
    next_check_at: Optional[datetime]
    last_change_event: Optional[ChangeEventSummary]
    change_count: int
    alerts_enabled: bool
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class DashboardSummaryResponse(BaseModel):
    services: list[ServiceSummary]
    total_services: int
    active_services: int
    recent_changes_count: int

