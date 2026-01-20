from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.saved_view import SortBy, SortOrder


class SavedViewBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    filter_tags: Optional[List[UUID]] = Field(None, description="List of tag IDs to filter by")
    filter_active: Optional[bool] = Field(None, description="Filter by active status")
    sort_by: SortBy = SortBy.name
    sort_order: SortOrder = SortOrder.asc


class SavedViewCreate(SavedViewBase):
    pass


class SavedViewUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    filter_tags: Optional[List[UUID]] = Field(None, description="List of tag IDs to filter by")
    filter_active: Optional[bool] = Field(None, description="Filter by active status")
    sort_by: Optional[SortBy] = None
    sort_order: Optional[SortOrder] = None


class SavedViewResponse(SavedViewBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
    
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if isinstance(data.get("filter_tags"), list):
            try:
                data["filter_tags"] = [UUID(tag_id) if isinstance(tag_id, str) else tag_id for tag_id in data["filter_tags"]]
            except (ValueError, TypeError):
                data["filter_tags"] = None
        return data
