import logging
from datetime import datetime

from telegram import Bot
from telegram.error import TelegramError

from config.settings import TOKEN
from models.notification import Notification, NotificationType, NotificationStatus

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=TOKEN)

    def format_message(self, event):
        """Форматирование сообщения для отправки"""
        days_left = (event.event_date - datetime.now()).days

        message = (
            f"🔔 <b>Напоминание о событии</b>\n\n"
            f"📌 Событие: {event.event_name}\n"
            f"📅 Дата: {event.event_date.strftime('%d.%m.%Y')}\n"
            f"⏰ До события: {days_left} дней\n"
        )

        if event.periodicity:
            message += f"🔄 Периодичность: {event.periodicity} мес.\n"

        return message

    def send_notification(self, db, event):
        """Отправка уведомления через Telegram"""
        try:
            message = self.format_message(event)

            # Получаем список Telegram ID из поля responsible_telegram_ids
            responsible_telegram_ids = event.responsible_telegram_ids.split(
                ",") if event.responsible_telegram_ids else []

            # Отправляем сообщение каждому получателю
            for telegram_id in responsible_telegram_ids:
                try:
                    self.bot.send_message(
                        chat_id=int(telegram_id),
                        text=message,
                        parse_mode='HTML'
                    )
                except TelegramError as e:
                    logger.error(f"Ошибка отправки уведомления пользователю {telegram_id}: {e}")

            # Создаем запись об уведомлении
            notification = Notification(
                event_id=event.event_id,
                user_id=event.creator_id,  # используем creator_id для связи
                type=NotificationType.TELEGRAM,
                scheduled_at=datetime.now()
            )

            # Обновляем статус
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now()

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
            if notification:
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(e)

        finally:
            if notification:
                db.add(notification)
                db.commit()