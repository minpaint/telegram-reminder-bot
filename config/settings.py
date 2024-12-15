import os

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
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

__all__ = ['TOKEN', 'ADMIN_ID', 'DATABASE_URL',
           'SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 'SMTP_PASSWORD']
