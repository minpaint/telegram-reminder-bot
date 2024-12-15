import logging
from datetime import datetime
from datetime import timedelta

from telegram import Update
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event
from .base import get_base_keyboard

logger = logging.getLogger(__name__)


def format_event_message(event, detailed=False):
    """Форматирование сообщения события"""
    default_time = datetime.min.time()
    event_time = event.event_date.time() if isinstance(event.event_date, datetime) else default_time
    base_message = (
        f"📅 Событие: {event.event_name}\n"
        f"🗓 Дата: {event.event_date.strftime('%d.%m.%Y')}\n"
        f"⏰ Время: {event_time.strftime('%H:%M')}\n"
        f"🔁 Повтор: {event.repeat_type or 'Нет'}\n"
        f"👤 Ответственный: @{event.responsible_telegram_ids.split(',')[0] if event.responsible_telegram_ids else 'не указан'}"
    )

    if detailed:
        extra_info = []
        if event.responsible_email:
            extra_info.append(f"📧 Email: {event.responsible_email}")
        if event.repeat_type == "Ежемесячно":
            extra_info.append(f"🔄 Периодичность: {event.periodicity} мес.")
        if event.remind_before:
            extra_info.append(f"⏰ Напомнить за {event.remind_before} дней")

        if extra_info:
            base_message += "\n" + "\n".join(extra_info)

    return base_message

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
            message_parts.append("⚠️ Просроченные события:\n")
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
            message_parts.append("📅 События на сегодня:\n")
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
            message_parts.append("🔔 Приближающиеся события:\n")
            grouped_upcoming = {}
            for event in upcoming_events:
                grouped_upcoming.setdefault(event.file_name, []).append(event)

            for file_name, events in grouped_upcoming.items():
                message_parts.append(f"📁 {file_name}\n")
                message_parts.append("━━━━━━━━━━━━━━━\n")
                for event in events:
                    event_date = event.event_date.strftime('%d.%m.%Y')
                    message_parts.append(f"📅 {event.event_name}: {event_date}\n")
                    message_parts.append(f"До события: {(event.event_date.date() - current_date).days} дней\n")

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
    logger.info(f"Запрос списка событий от пользователя {user_id}")

    db = SessionLocal()
    try:
        events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True
        ).order_by(Event.file_name, Event.event_date).all()

        if not events:
            update.message.reply_text(
                "📭 У вас нет активных событий.\n"
                "Используйте команду 'Добавить файл' для загрузки событий."
            )
            return

        # Группировка событий по файлам
        events_by_file = {}
        for event in events:
            file_name = event.file_name or "Другие события"
            if file_name not in events_by_file:
                events_by_file[file_name] = []
            events_by_file[file_name].append(event)

        # Формирование сообщения
        message_parts = []

        # Обработка всех файлов
        for file_name, file_events in sorted(events_by_file.items()):
            message_parts.append(f"\n📁 {file_name}\n")
            message_parts.append("━━━━━━━━━━━━━━━\n\n")

            for event in sorted(file_events, key=lambda x: x.event_date):
                days_left = (event.event_date.date() - datetime.now().date()).days

                # Определяем статус события
                if days_left < 0:
                    status = "⚠️"  # просрочено
                elif days_left <= 3:
                    status = "❗️"  # срочно
                else:
                    status = "📌"  # обычное

                # Основная информация о событии
                message_parts.append(
                    f"{status} {event.event_name}\n"
                    f"📅 {event.event_date.strftime('%d.%m.%Y')}"
                )

                # Добавляем количество дней, если событие не сегодня
                if days_left != 0:
                    if days_left < 0:
                        message_parts.append(f" (просрочено на {abs(days_left)} дн.)")
                    else:
                        message_parts.append(f" (через {days_left} дн.)")

                message_parts.append("\n")

                # Дополнительная информация (без email)
                if event.responsible_telegram_ids and event.responsible_telegram_ids != "@не указан":
                    message_parts.append(f"👤 {event.responsible_telegram_ids}\n")
                if event.repeat_type and event.repeat_type.lower() != "нет":
                    message_parts.append(f"🔄 {event.repeat_type}")
                    if event.periodicity:
                        message_parts.append(f" ({event.periodicity} мес.)")
                    message_parts.append("\n")

                message_parts.append("\n")

        # Добавляем статистику
        total_events = len(events)
        urgent_events = sum(1 for e in events if 0 <= (e.event_date.date() - datetime.now().date()).days <= 3)
        overdue_events = sum(1 for e in events if (e.event_date.date() - datetime.now().date()).days < 0)

        if total_events > 0:
            stats = (
                f"\n📊 Статистика:\n"
                f"📌 Всего событий: {total_events}\n"
            )
            if urgent_events > 0:
                stats += f"❗️ Срочных (≤3 дня): {urgent_events}\n"
            if overdue_events > 0:
                stats += f"⚠️ Просроченных: {overdue_events}\n"
            message_parts.append(stats)

        # Отправка сообщения
        final_message = "".join(message_parts)

        # Разбиваем сообщение на части, если оно слишком длинное
        if len(final_message) > 4096:
            for i in range(0, len(final_message), 4096):
                update.message.reply_text(
                    final_message[i:i + 4096],
                    parse_mode='HTML'
                )
        else:
            update.message.reply_text(final_message, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Ошибка при показе событий: {e}", exc_info=True)
        update.message.reply_text(
            "❌ Произошла ошибка при получении списка событий.\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
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