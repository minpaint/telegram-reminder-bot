import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event
from .base import get_base_keyboard, format_event_message
from .events import delete_event_request, update_event_request

logger = logging.getLogger(__name__)


def handle_menu_choice(update: Update, context: CallbackContext):
    """Обработка выбора в меню"""
    text = update.message.text

    if text == "📂 Добавить файл":
        handle_add_file(update, context)
    elif text == "🔔 Напоминания":
        reminders_command(update, context)
    elif text == "📋 Мои события":
        show_events(update, context)
    elif text == "✏️ Изменить событие":
        update_event_request(update, context)
    elif text == "🗑 Удалить событие":
        delete_event_request(update, context)
    elif text == "🔄 Перезапустить":
        restart_command(update, context)


def start_command(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    db = SessionLocal()
    try:
        message = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Я помогу вам управлять событиями и напоминаниями.\n\n"
            "Используйте кнопки меню для работы с событиями:"
        )
        keyboard = get_base_keyboard(user.id)
        update.message.reply_text(message, reply_markup=keyboard)
    finally:
        db.close()


def reminders_command(update: Update, context: CallbackContext):
    """Показ напоминаний"""
    user_id = update.effective_user.id
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    today_end = today_start + timedelta(days=1)

    db = SessionLocal()
    try:
        events_today = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.next_reminder >= today_start,
            Event.next_reminder < today_end,
            Event.is_active == True
        ).all()

        message = "🔔 Напоминания на сегодня:\n\n"

        if not events_today:
            message += "Нет активных напоминаний"
        else:
            for event in events_today:
                message += format_event_message(event) + "\n\n"

        update.message.reply_text(message)
    finally:
        db.close()


def show_events(update: Update, context: CallbackContext):
    """Показ списка событий пользователя с группировкой по файлам"""
    user_id = update.effective_user.id
    db = SessionLocal()
    try:
        events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True
        ).order_by(Event.file_name, Event.event_date).all()

        if not events:
            update.message.reply_text("📭 У вас нет активных событий.")
            return

        events_by_file = {}
        for event in events:
            file_name = event.file_name or "Другие события"
            if file_name not in events_by_file:
                events_by_file[file_name] = []
            events_by_file[file_name].append(event)

        message_parts = ["📋 Ваши события:\n\n"]

        if "Другие события" in events_by_file:
            message_parts.append("📝 Другие события\n")
            message_parts.append("━━━━━━━━━━━━━━━\n")
            for event in sorted(events_by_file["Другие события"],
                                key=lambda x: x.event_date):
                message_parts.append(format_event_message(event) + "\n\n")
            message_parts.append("\n")
            del events_by_file["Другие события"]

        for file_name, file_events in sorted(events_by_file.items()):
            message_parts.append(f"📁 {file_name}\n")
            message_parts.append("━━━━━━━━━━━━━━━\n")

            for event in sorted(file_events, key=lambda x: x.event_date):
                message_parts.append(format_event_message(event) + "\n\n")

            message_parts.append("\n")

        final_message = "".join(message_parts)

        if len(final_message) > 4096:
            for i in range(0, len(final_message), 4096):
                update.message.reply_text(final_message[i:i + 4096])
        else:
            update.message.reply_text(final_message)

    except Exception as e:
        logger.error(f"Ошибка при показе событий: {e}", exc_info=True)
        update.message.reply_text("❌ Ошибка при получении списка событий")
    finally:
        db.close()


def restart_command(update: Update, context: CallbackContext):
    """Перезапуск бота"""
    user_id = update.effective_user.id
    message = "🔄 Бот перезапущен."
    keyboard = get_base_keyboard(user_id)
    update.message.reply_text(message, reply_markup=keyboard)


def handle_add_file(update: Update, context: CallbackContext):
    """Обработка команды 'Добавить файл'"""
    update.message.reply_text(
        "📤 Пожалуйста, загрузите файл Excel (.xlsx) со списком событий.\n\n"
        "Формат файла:\n"
        "- Событие\n"
        "- Дата наступления (ДД.ММ.ГГГГ)\n"
        "- Время наступления (ЧЧ:ММ)\n"
        "- За сколько дней напомнить\n"
        "- Повтор события (Нет/Ежемесячно)\n"
        "- Периодичность (мес)\n"
        "- Ответственный (@username)\n"
        "- Email ответственного"
    )