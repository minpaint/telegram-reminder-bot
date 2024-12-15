import os
from datetime import datetime

from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Основные настройки
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# База данных
DATABASE_URL = "sqlite:///data/reminder_bot.db"

# Директории
EXCEL_TEMP_DIR = "temp_files"
LOG_DIR = "logs"
DATA_DIR = "data"

# Создаём необходимые директории
for dir_path in [EXCEL_TEMP_DIR, LOG_DIR, DATA_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Email settings
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# Настройки уведомлений
NOTIFICATION_TIME = "09:00"  # Отправлять все уведомления в 9:00


def schedule_notification(event):
    """
    Планирование отправки уведомления

    Args:
        event: Объект события из базы данных
    """
    from services.scheduler.manager import SchedulerManager

    notification_date = event.next_reminder.date()
    notification_time = datetime.strptime(NOTIFICATION_TIME, "%H:%M").time()
    send_at = datetime.combine(notification_date, notification_time)

    scheduler = SchedulerManager()
    scheduler.add_notification_job(
        f"notify_{event.event_id}",
        send_notification,
        run_date=send_at,
        event_id=event.event_id
    )


def send_notification(event_id):
    """
    Функция отправки уведомления

    Args:
        event_id: ID события
    """
    from core.database import SessionLocal
    from models import Event
    from services.notifications.telegram import TelegramNotifier
    from services.notifications.email import EmailNotifier

    db = SessionLocal()
    try:
        event = db.query(Event).filter_by(event_id=event_id).first()
        if not event:
            return

        # Отправка уведомления в Telegram
        if event.responsible_telegram_ids:
            telegram_notifier = TelegramNotifier()
            telegram_notifier.send_notification(db, event)

        # Отправка уведомления на email
        if event.responsible_email:
            email_notifier = EmailNotifier()
            email_notifier.send_notification(db, event)

    finally:
        db.close()


# Настройки тестового режима
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"
TEST_TELEGRAM_ID = os.getenv("TEST_TELEGRAM_ID")
TEST_EMAIL = os.getenv("TEST_EMAIL")

__all__ = [
    'TOKEN', 'ADMIN_ID', 'DATABASE_URL',
    'SMTP_SERVER', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SENDER_EMAIL',
    'NOTIFICATION_TIME', 'schedule_notification', 'TEST_MODE', 'TEST_TELEGRAM_ID', 'TEST_EMAIL'
]