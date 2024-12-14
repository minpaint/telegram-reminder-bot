import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event
from .base import get_base_keyboard, format_event_message

logger = logging.getLogger(__name__)


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
    """Показать активные напоминания"""
    user_id = update.effective_user.id
    current_date = datetime.now().date()
    one_month_ahead = current_date + timedelta(days=30)  # ограничение на один месяц
    db = SessionLocal()
    try:
        overdue_events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True,
            Event.event_date < current_date
        ).order_by(Event.event_date).all()

        today_events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True,
            Event.event_date == current_date
        ).order_by(Event.event_date).all()

        upcoming_events = []
        all_future_events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True,
            Event.event_date > current_date,
            Event.event_date <= one_month_ahead
        ).order_by(Event.event_date).all()

        for event in all_future_events:
            remind_date = event.event_date - timedelta(days=event.remind_before)
            if current_date >= remind_date.date():
                upcoming_events.append(event)

        logger.info(
            f"Найдено: просрочено - {len(overdue_events)}, сегодня - {len(today_events)}, предстоящих - {len(upcoming_events)}")

        if not any([overdue_events, today_events, upcoming_events]):
            update.message.reply_text("📭 Нет активных напоминаний")
            return

        message_parts = []

        if overdue_events:
            message_parts.append("<b>⚠️ Просроченные события:</b>\n")
            grouped_overdue = {}
            for event in overdue_events:
                grouped_overdue.setdefault(event.file_name, []).append(event)

            for file_name, events in grouped_overdue.items():
                message_parts.append(f"📁 {file_name}\n")
                message_parts.append("━━━━━━━━━━━━━━━\n")
                for event in events:
                    event_date = event.event_date.strftime('%d.%m.%Y')
                    message_parts.append(f"📅 {event.event_name}: {event_date}\n")

        if today_events:
            message_parts.append("<b>📅 События на сегодня:</b>\n")
            grouped_today = {}
            for event in today_events:
                grouped_today.setdefault(event.file_name, []).append(event)

            for file_name, events in grouped_today.items():
                message_parts.append(f"📁 {file_name}\n")
                message_parts.append("━━━━━━━━━━━━━━━\n")
                for event in events:
                    event_date = event.event_date.strftime('%d.%m.%Y')
                    message_parts.append(f"📅 {event.event_name}: {event_date}\n")

        if upcoming_events:
            message_parts.append("<b>🔔 Приближающиеся события:</b>\n")
            grouped_upcoming = {}
            for event in upcoming_events:
                grouped_upcoming.setdefault(event.file_name, []).append(event)

            for file_name, events in grouped_upcoming.items():
                message_parts.append(f"📁 {file_name}\n")
                message_parts.append("━━━━━━━━━━━━━━━\n")
                for event in events:
                    event_date = event.event_date.strftime('%d.%m.%Y')
                    days_left = (event.event_date.date() - current_date).days
                    message_parts.append(f"📅 {event.event_name}: {event_date}\n")
                    message_parts.append(f"До события: {days_left} дней\n")

        final_message = "".join(message_parts)
        if len(final_message) > 4096:
            for i in range(0, len(final_message), 4096):
                update.message.reply_text(final_message[i:i + 4096], parse_mode='HTML')
        else:
            update.message.reply_text(final_message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Ошибка при показе напоминаний: {e}")
        update.message.reply_text("❌ Ошибка при получении напоминаний")
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
        ).all()

        if not events:
            update.message.reply_text("📭 У вас нет активных событий.")
            return

        events_by_file = {}
        for event in events:
            # Преобразуем дату к datetime с временем по умолчанию
            if isinstance(event.event_date, str):
                try:
                    event.event_date = datetime.strptime(event.event_date, "%Y-%m-%d").replace(hour=0, minute=0,
                                                                                               second=0)
                except ValueError:
                    try:
                        event.event_date = datetime.strptime(event.event_date, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            event.event_date = datetime.strptime(event.event_date, "%d.%m.%Y")
                        except ValueError as e:
                            logger.error(f"Не удалось распарсить дату {event.event_date}, ошибка {e}")
                            continue
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