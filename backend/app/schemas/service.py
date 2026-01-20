from pydantic import BaseModel, HttpUrl, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.service import CheckFrequency
from app.schemas.tag import TagResponse


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1)
    check_frequency: CheckFrequency = CheckFrequency.daily

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class ServiceCreate(ServiceBase):
    tag_ids: Optional[List[UUID]] = Field(None, description="List of tag IDs to assign to the service")


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = Field(None, min_length=1)
    check_frequency: Optional[CheckFrequency] = None
    is_active: Optional[bool] = None
    alerts_enabled: Optional[bool] = None
    alert_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    slack_webhook_url: Optional[str] = Field(None)
    discord_webhook_url: Optional[str] = Field(None)
    tag_ids: Optional[List[UUID]] = Field(None, description="List of tag IDs to assign to the service")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class ServiceResponse(ServiceBase):
    id: UUID
    user_id: UUID
    last_checked_at: Optional[datetime] = None
    is_active: bool
    alerts_enabled: bool
    alert_confidence_threshold: float
    slack_webhook_url: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    alert_count_24h: int = 0
    created_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True

