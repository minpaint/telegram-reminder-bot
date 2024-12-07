import os

# Основная структура проекта
project_structure = {
    "config": ["__init__.py", "settings.py", "logging_config.py"],
    "core": ["__init__.py", "database.py", "exceptions.py"],
    "handlers": ["__init__.py", "commands.py", "events.py", "files.py"],
    "logs": [],  # Лог-файлы будут создаваться автоматически
    "migrations": ["__init__.py"],
    "models": ["__init__.py", "user.py", "event.py", "notification.py"],
    "services": {
        "excel": ["__init__.py", "parser.py", "validator.py"],
        "notifications": ["__init__.py", "base.py", "telegram.py", "email.py"],
        "scheduler": ["__init__.py", "manager.py", "tasks.py"],
    },
    "temp_files": [],  # Для временных файлов
    "templates": {
        "email": ["reminder.html", "overdue.html"],
        "telegram": ["reminder.txt", "overdue.txt"],
    },
    "tests": ["__init__.py", "test_excel.py", "test_notifications.py", "test_handlers.py"],
    "utils": ["__init__.py", "decorators.py", "formatters.py", "validators.py"],
    "data": [],  # Для базы данных SQLite
}

# Базовые файлы в корне проекта
base_files = {
    ".env": "DATABASE_URL=sqlite:///data/reminder_bot.db\nBOT_TOKEN=your_telegram_bot_token\n",
    ".gitignore": ".venv/\n__pycache__/\n*.pyc\n*.pyo\n*.log\n.env\n",
    "requirements.txt": """python-telegram-bot==13.14
pandas
apscheduler==3.6.3
SQLAlchemy
urllib3==1.26.15
python-dotenv
psutil==5.9.5
pytz
email-validator
alembic""",
    "README.md": "# Telegram Reminder Bot\n\nA bot to manage reminders and notifications via Telegram.",
}


# Создание структуры проекта
def create_structure(base_path="."):
    for folder, contents in project_structure.items():
        folder_path = os.path.join(base_path, folder)
        os.makedirs(folder_path, exist_ok=True)

        if isinstance(contents, list):  # Простая папка с файлами
            for file_name in contents:
                file_path = os.path.join(folder_path, file_name)
                if not os.path.exists(file_path):
                    with open(file_path, "w") as f:
                        f.write(f"# {file_name} placeholder")
        elif isinstance(contents, dict):  # Вложенные папки
            for subfolder, subfiles in contents.items():
                subfolder_path = os.path.join(folder_path, subfolder)
                os.makedirs(subfolder_path, exist_ok=True)
                for file_name in subfiles:
                    file_path = os.path.join(subfolder_path, file_name)
                    if not os.path.exists(file_path):
                        with open(file_path, "w") as f:
                            f.write(f"# {file_name} placeholder")

    for file_name, file_content in base_files.items():  # Создание базовых файлов
        file_path = os.path.join(base_path, file_name)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(file_content)


if __name__ == "__main__":
    create_structure()
    print("✅ Проект успешно создан!")
