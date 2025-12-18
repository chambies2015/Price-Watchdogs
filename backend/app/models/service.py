from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class CheckFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    check_frequency = Column(Enum(CheckFrequency), default=CheckFrequency.daily, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    last_snapshot_id = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="services")
    snapshots = relationship("Snapshot", back_populates="service", cascade="all, delete-orphan")
    change_events = relationship("ChangeEvent", back_populates="service", cascade="all, delete-orphan")

