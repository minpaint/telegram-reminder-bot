from datetime import datetime

from core.database import SessionLocal
from models import NotificationType, NotificationStatus
from services.notifications.email import EmailNotifier
from services.notifications.telegram import TelegramNotifier


def send_notification(event_id, user_id):
    """Отправка уведомления"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter_by(event_id=event_id).first()
        user = db.query(User).filter_by(user_id=user_id).first()

        if not event or not user:
            return

        telegram_notifier = TelegramNotifier()
        email_notifier = EmailNotifier()

        # Формируем сообщение
        message = f"""
        🔔 <b>Напоминание</b>

        Событие: {event.event_name}
        Дата: {event.event_date.strftime('%d.%m.%Y')}
        До события осталось: {(event.event_date - datetime.now()).days} дней
        """

        # Отправляем уведомления
        try:
            telegram_notifier.send(user, event, message)
            telegram_notifier.log_notification(
                db, user.user_id, event.event_id,
                NotificationType.TELEGRAM,
                NotificationStatus.SENT
            )
        except Exception as e:
            telegram_notifier.log_notification(
                db, user.user_id, event.event_id,
                NotificationType.TELEGRAM,
                NotificationStatus.FAILED,
                str(e)
            )

        if user.email:
            try:
                email_notifier.send(user, event, message)
                email_notifier.log_notification(
                    db, user.user_id, event.event_id,
                    NotificationType.EMAIL,
                    NotificationStatus.SENT
                )
            except Exception as e:
                email_notifier.log_notification(
                    db, user.user_id, event.event_id,
                    NotificationType.EMAIL,
                    NotificationStatus.FAILED,
                    str(e)
                )

    finally:
        db.close()
