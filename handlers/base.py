from datetime import datetime

from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_base_keyboard(user_id):
    """Создание клавиатуры меню"""
    keyboard = [
        [KeyboardButton("🔔 Напоминания"), KeyboardButton("📋 Мои события")],
        [KeyboardButton("📂 Добавить файл"), KeyboardButton("✏️ Изменить событие")],
        [KeyboardButton("🗑 Удалить событие"), KeyboardButton("🔄 Перезапустить")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


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