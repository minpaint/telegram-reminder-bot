import logging

logger = logging.getLogger(__name__)


def format_event_message(event):
    """
    Форматирует сообщение о событии.
    :param event: объект события
    :return: отформатированное сообщение
    """
    try:
        event_date = event.event_date.strftime('%d.%m.%Y')
        message = f"Название: {event.event_name}\nДата: {event_date}"
        if event.file_name:
            message += f"\nФайл: {event.file_name}"
        if event.remind_before:
            message += f"\nНапоминание за {event.remind_before} дней"
        return message
    except AttributeError as e:
        logger.error(f"Ошибка форматирования события: {e}")
        return "❌ Ошибка при обработке события."

def format_events_with_numbers(events):
    """
    Форматирование событий с номерами для отображения.
    :param events: список событий
    :return: отформатированное сообщение
    """
    grouped_events = {}
    for event in events:
        grouped_events.setdefault(event.file_name, []).append(event)

    message = ""
    for idx, (file_name, file_events) in enumerate(grouped_events.items(), start=1):
        message += f"📁 {idx}. {file_name}\n"
        for sub_idx, event in enumerate(file_events, start=1):
            try:
                event_date = event.event_date.strftime('%d.%m.%Y')
                event_time = event.event_time.strftime('%H:%M') if event.event_time else "Без времени"
                message += f"📌 {idx}.{sub_idx} {event.event_name}: {event_date} {event_time}\n"
            except AttributeError as e:
                logger.error(f"Ошибка при форматировании события {event.event_name}: {e}")
                message += f"📌 {idx}.{sub_idx} {event.event_name}: ❌ Ошибка при форматировании\n"
    return message.strip()
