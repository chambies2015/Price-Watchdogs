from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class ChangeType(str, enum.Enum):
    price_increase = "price_increase"
    price_decrease = "price_decrease"
    new_plan_added = "new_plan_added"
    plan_removed = "plan_removed"
    free_tier_removed = "free_tier_removed"
    unknown = "unknown"


class ChangeEvent(Base):
    __tablename__ = "change_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    old_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("snapshots.id"), nullable=True)
    new_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("snapshots.id"), nullable=False)
    change_type = Column(Enum(ChangeType), nullable=False)
    summary = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    service = relationship("Service", back_populates="change_events")
    old_snapshot = relationship("Snapshot", foreign_keys=[old_snapshot_id], back_populates="old_change_events")
    new_snapshot = relationship("Snapshot", foreign_keys=[new_snapshot_id], back_populates="new_change_events")
    alerts = relationship("Alert", back_populates="change_event", cascade="all, delete-orphan")

