from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class CheckFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    twice_daily = "twice_daily"


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
    alerts_enabled = Column(Boolean, default=True, nullable=False)
    alert_confidence_threshold = Column(Float, default=0.6, nullable=False)
    slack_webhook_url = Column(String, nullable=True)
    discord_webhook_url = Column(String, nullable=True)
    alert_count_24h = Column(Integer, default=0, nullable=False)
    last_alert_reset = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="services")
    snapshots = relationship("Snapshot", back_populates="service", cascade="all, delete-orphan")
    change_events = relationship("ChangeEvent", back_populates="service", cascade="all, delete-orphan")

