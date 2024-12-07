from abc import ABC, abstractmethod
from datetime import datetime

from models import Notification, NotificationStatus


class BaseNotifier(ABC):
    """Базовый класс для отправки уведомлений"""

    @abstractmethod
    def send(self, user, event, message):
        """Отправка уведомления"""
        pass

    def log_notification(self, db, user_id, event_id, notification_type, status, error=None):
        """Логирование отправки уведомления"""
        notification = Notification(
            user_id=user_id,
            event_id=event_id,
            type=notification_type,
            status=status,
            sent_at=datetime.utcnow() if status == NotificationStatus.SENT else None,
            error_message=error
        )
        db.add(notification)
        db.commit()
        return notification
