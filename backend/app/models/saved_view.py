from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class SortBy(str, enum.Enum):
    name = "name"
    created_at = "created_at"
    last_checked_at = "last_checked_at"


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"


class SavedView(Base):
    __tablename__ = "saved_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    filter_tags = Column(JSON, nullable=True)
    filter_active = Column(Boolean, nullable=True)
    sort_by = Column(Enum(SortBy), default=SortBy.name, nullable=False)
    sort_order = Column(Enum(SortOrder), default=SortOrder.asc, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="saved_views")
