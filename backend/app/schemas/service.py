from pydantic import BaseModel, HttpUrl, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.service import CheckFrequency


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
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = Field(None, min_length=1)
    check_frequency: Optional[CheckFrequency] = None
    is_active: Optional[bool] = None

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
    created_at: datetime

    class Config:
        from_attributes = True

