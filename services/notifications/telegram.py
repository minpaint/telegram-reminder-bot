import logging
from datetime import datetime

from telegram import Bot
from telegram.error import TelegramError

from config.settings import TOKEN
from models import Notification, NotificationType, NotificationStatus

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=TOKEN)

    def format_message(self, event):
        """Форматирование сообщения для отправки"""
        days_left = (event.event_date - datetime.now()).days

        message = (
            f"🔔 <b>Напоминание о событии</b>

            "
            f"📌 Событие: {event.event_name}
            "
            f"📅 Дата: {event.event_date.strftime('%d.%m.%Y')}
            "
            f"⏰ До события: {days_left} дней
            "
        )

        if event.periodicity:
            message += f"🔄 Периодичность: {event.periodicity} мес.


"

return message


def send_notification(self, db, user_id, event):
    """Отправка уведомления через Telegram"""
    try:
        message = self.format_message(event)

        # Создаем запись об уведомлении
        notification = Notification(
            event_id=event.event_id,
            user_id=user_id,
            type=NotificationType.TELEGRAM,
            scheduled_at=datetime.now()
        )

        # Пробуем отправить сообщение
        self.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )

        # Обновляем статус
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now()

    except TelegramError as e:
        logger.error(f"Telegram error for user {user_id}: {e}")
        if notification:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)

    except Exception as e:
        logger.error(f"Error sending telegram notification: {e}")
        if notification:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)

    finally:
        if notification:
            db.add(notification)
            db.commit()
