import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event
from services.scheduler.tasks import send_notification

logger = logging.getLogger(__name__)

def get_base_keyboard(user_id):
    """Создание клавиатуры меню"""
    keyboard = [
        [KeyboardButton("🔔 Напоминания"), KeyboardButton("📋 Мои события")],
        [KeyboardButton("📂 Добавить файл"), KeyboardButton("✏️ Изменить событие")],
        [KeyboardButton("🗑 Удалить событие"), KeyboardButton("📢 Отправить напоминание")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


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

    try:
        event_id = int(query.data.split('_')[-1])
        user_id = query.from_user.id
        logger.info(f"Ручная отправка напоминания для события {event_id}")
        send_notification(event_id, user_id)
        query.edit_message_text(f"✅ Напоминание для события {event_id} отправлено.")
        logger.info(f"Ручное уведомление для события {event_id} успешно отправлено")

    except AttributeError as e:
        logger.error(f"Ошибка при ручной отправке уведомления: {e}", exc_info=True)
        query.edit_message_text(f"❌ Ошибка при отправке напоминания для события {event_id}.")
    except Exception as e:
        logger.error(f"Ошибка при ручной отправке уведомления: {e}", exc_info=True)
        query.edit_message_text(f"❌ Ошибка при отправке напоминания для события {event_id}.")
