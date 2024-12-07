def format_events_with_numbers(events):
    """Форматирование событий с номерами для отображения."""
    grouped_events = {}
    for event in events:
        grouped_events.setdefault(event.file_name, []).append(event)

    message = ""
    for idx, (file_name, file_events) in enumerate(grouped_events.items(), start=1):
        message += f"📁 {idx}. {file_name}\n"
        for sub_idx, event in enumerate(file_events, start=1):
            message += (
                f"📌 {idx}.{sub_idx} {event.event_name}: "
                f"{event.event_date.strftime('%d.%m.%Y')} {event.event_time.strftime('%H:%M')}\n"
            )
    return message.strip()
