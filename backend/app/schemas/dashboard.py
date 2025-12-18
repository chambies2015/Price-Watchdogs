from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.change_event import ChangeType
from app.schemas.service import ServiceResponse


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
    last_checked_at: Optional[datetime]
    last_change_event: Optional[ChangeEventSummary]
    change_count: int
    alerts_enabled: bool

    class Config:
        from_attributes = True


class DashboardSummaryResponse(BaseModel):
    services: list[ServiceSummary]
    total_services: int
    active_services: int
    recent_changes_count: int

