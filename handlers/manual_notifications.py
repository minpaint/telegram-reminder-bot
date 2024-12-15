import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event, User, Notification, NotificationType, NotificationStatus
from services.notifications.email import EmailNotifier
from services.notifications.telegram import TelegramNotifier

logger = logging.getLogger(__name__)


def manual_notification_request(update: Update, context: CallbackContext):
    """Запрос на ручную отправку напоминаний."""
    user_id = update.effective_user.id
    logger.info(f"Запрос на ручную отправку напоминания от пользователя {user_id}")

    db = SessionLocal()
    try:
        events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True
        ).order_by(Event.file_name, Event.event_date).all()

        logger.info(f"Найдено {len(events)} событий")

        if not events:
            update.message.reply_text("📭 Нет активных событий для отправки напоминаний.")
            return

        events_by_file = {}
        for event in events:
            try:
                file_name = event.file_name or "Другие события"
                if file_name not in events_by_file:
                    events_by_file[file_name] = []
                events_by_file[file_name].append(event)
            except Exception as e:
                logger.error(f"Ошибка при обработке события {event.event_id}: {e}")

        keyboard = []

        try:
            if "Другие события" in events_by_file:
                keyboard.append([InlineKeyboardButton("📝 Другие события", callback_data="header_other")])
                for event in sorted(events_by_file["Другие события"], key=lambda x: x.event_date):
                    button_text = f"{event.event_name}: {event.event_date.strftime('%d.%m.%Y')}"
                    callback_data = f"manual_send_{event.event_id}"
                    keyboard.append([InlineKeyboardButton(f"Отправить {button_text}", callback_data=callback_data)])
                del events_by_file["Другие события"]

            for file_name, file_events in sorted(events_by_file.items()):
                keyboard.append([InlineKeyboardButton(f"📁 {file_name}", callback_data=f"header_{file_name}")])
                for event in sorted(file_events, key=lambda x: x.event_date):
                    button_text = f"{event.event_name}: {event.event_date.strftime('%d.%m.%Y')}"
                    callback_data = f"manual_send_{event.event_id}"
                    keyboard.append([InlineKeyboardButton(f"Отправить {button_text}", callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("📢 Выберите событие для отправки напоминания:", reply_markup=reply_markup)
            logger.info("Сообщение отправлено успешно")

        except Exception as e:
            logger.error(f"Ошибка при создании клавиатуры: {e}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Общая ошибка: {e}", exc_info=True)
        update.message.reply_text("❌ Произошла ошибка при получении списка событий")
    finally:
        db.close()


def handle_manual_notification_callback(update: Update, context: CallbackContext):
    """Обработка отправки ручного напоминания."""
    query = update.callback_query
    logger.info(f"Получен callback ручной отправки: {query.data}")
    query.answer()

    if query.data.startswith("header"):
        return

    db = SessionLocal()
    try:
        event_id = int(query.data.split('_')[-1])
        user_id = query.from_user.id

        event = db.query(Event).filter(Event.event_id == event_id).first()
        user = db.query(User).filter(User.user_id == user_id).first()

        if not event or not user:
            query.edit_message_text(f"❌ Событие или пользователь не найдены")
            return

        logger.info(f"Ручная отправка напоминания для события {event_id}")

        telegram_notifier = TelegramNotifier()
        email_notifier = EmailNotifier()

        message = f"""
🔔 <b>Напоминание</b>

Событие: {event.event_name}
Дата: {event.event_date.strftime('%d.%m.%Y')}
До события осталось: {(event.event_date - datetime.now()).days} дней
"""

        try:
            telegram_notifier.send_notification(db, event)
            notification = Notification(
                user_id=user.user_id,
                event_id=event.event_id,
                type=NotificationType.TELEGRAM,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow()
            )
            db.add(notification)
            logger.info("Уведомление в телеграм отправлено")
        except Exception as e:
            notification = Notification(
                user_id=user.user_id,
                event_id=event.event_id,
                type=NotificationType.TELEGRAM,
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
            db.add(notification)
            logger.error(f"Ошибка отправки уведомления пользователю: {e}")

        if user.email:
            try:
                email_notifier.send_notification(db, event)
                notification = Notification(
                    user_id=user.user_id,
                    event_id=event.event_id,
                    type=NotificationType.EMAIL,
                    status=NotificationStatus.SENT,
                    sent_at=datetime.utcnow()
                )
                db.add(notification)
                logger.info("Уведомление на email отправлено")

            except Exception as e:
                notification = Notification(
                    user_id=user.user_id,
                    event_id=event.event_id,
                    type=NotificationType.EMAIL,
                    status=NotificationStatus.FAILED,
                    error_message=str(e)
                )
                db.add(notification)
                logger.error(f"Ошибка отправки уведомления на email: {e}")

        db.commit()
        query.edit_message_text(f"✅ Напоминание для события {event_id} отправлено.")
        logger.info(f"Ручное уведомление для события {event_id} успешно отправлено")
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при ручной отправке уведомления: {e}")
        query.edit_message_text(f"❌ Ошибка при отправке напоминания для события {event_id}.")
    finally:
        db.close()
