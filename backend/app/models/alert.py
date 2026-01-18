from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class AlertChannel(str, enum.Enum):
    email = "email"
    slack = "slack"
    discord = "discord"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_event_id = Column(UUID(as_uuid=True), ForeignKey("change_events.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime, nullable=True)
    channel = Column(Enum(AlertChannel), default=AlertChannel.email, nullable=False)

    change_event = relationship("ChangeEvent", back_populates="alerts")
    user = relationship("User", back_populates="alerts")

