from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from core.database import Base


class NotificationType(str, Enum):
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
