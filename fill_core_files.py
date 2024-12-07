import os


def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def create_main_file():
    main_content = '''import os
import logging
from dotenv import load_dotenv
from telegram.ext import Updater
from handlers import setup_handlers
from core.database import init_db
from services.scheduler.manager import SchedulerManager
from config.settings import TOKEN, ADMIN_ID

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f'Update "{update}" caused error "{context.error}"')

    # Отправляем уведомление админу об ошибке
    if ADMIN_ID:
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔴 Произошла ошибка:\\n{context.error}"
        )

def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация бота
        updater = Updater(token=TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        # Регистрация обработчиков
        setup_handlers(dispatcher)

        # Добавляем обработчик ошибок
        dispatcher.add_error_handler(error_handler)

        # Инициализация планировщика
        scheduler = SchedulerManager()
        scheduler.start()
        logger.info("Scheduler started")

        # Запуск бота
        updater.start_polling()
        logger.info("Bot started polling")

        # Уведомляем админа о запуске бота
        if ADMIN_ID:
            updater.bot.send_message(
                chat_id=ADMIN_ID,
                text="🟢 Бот успешно запущен и готов к работе!"
            )

        # Ожидаем остановки бота
        updater.idle()

    except Exception as e:
        logger.error(f"Critical error: {e}")
        if ADMIN_ID:
            try:
                updater.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🔴 Критическая ошибка: {e}"
                )
            except:
                pass
        raise

if __name__ == "__main__":
    # Загружаем переменные окружения
    load_dotenv()

    # Проверяем наличие токена
    if not TOKEN:
        logger.error("Telegram token not found in environment variables")
        exit(1)

    # Инициализируем базу данных
    init_db()

    # Запускаем бота
    main()
'''

    try:
        # Записываем main.py
        write_file('main.py', main_content)
        print(f"✅ Создан файл: main.py")

        print("\n✅ Основной файл успешно создан!")
        print("\nТеперь у вас готова полная структура проекта.")
        print("\nСледующие шаги:")
        print("1. Проверьте все созданные файлы")
        print("2. Убедитесь, что все зависимости установлены")
        print("3. Проверьте настройки в .env файле")
        print("4. Запустите бота: python main.py")

    except Exception as e:
        print(f"\n❌ Ошибка при создании файла: {e}")


if __name__ == "__main__":
    create_main_file()
