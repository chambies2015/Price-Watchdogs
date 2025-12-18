from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    raw_html_hash = Column(String, nullable=False)
    normalized_content_hash = Column(String, nullable=False)
    normalized_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    service = relationship("Service", back_populates="snapshots")
    old_change_events = relationship("ChangeEvent", foreign_keys="ChangeEvent.old_snapshot_id", back_populates="old_snapshot")
    new_change_events = relationship("ChangeEvent", foreign_keys="ChangeEvent.new_snapshot_id", back_populates="new_snapshot")

