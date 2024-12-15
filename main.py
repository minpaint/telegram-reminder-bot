import logging
import os

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from handlers import (
    start_command,
    show_events,
    reminders_command,
    delete_event_request,
    update_event_request,
    handle_add_file,
    handle_delete_callback,
    handle_update_callback,
    handle_document,
    handle_new_date,
    manual_notification_request,
    handle_manual_notification_callback
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def setup_handlers(dp):
    """Регистрация обработчиков"""

    # Команды
    dp.add_handler(CommandHandler("start", start_command))

    # Обработка файлов
    dp.add_handler(MessageHandler(
        Filters.document.file_extension('xlsx'),
        handle_document
    ))

    # Обработка текстовых команд
    dp.add_handler(MessageHandler(
        Filters.regex('^📋 Мои события$'),
        show_events
    ))

    dp.add_handler(MessageHandler(
        Filters.regex('^🔔 Напоминания$'),
        reminders_command
    ))

    dp.add_handler(MessageHandler(
        Filters.regex('^🗑 Удалить событие$'),
        delete_event_request
    ))

    dp.add_handler(MessageHandler(
        Filters.regex('^✏️ Изменить событие$'),
        update_event_request
    ))

    dp.add_handler(MessageHandler(
        Filters.regex('^📂 Добавить файл$'),
        handle_add_file
    ))

    # Обработка ручных уведомлений
    dp.add_handler(MessageHandler(
        Filters.regex('^📢 Отправить напоминание$'),
        manual_notification_request
    ))

    # Обработка callback-запросов
    dp.add_handler(CallbackQueryHandler(
        handle_delete_callback,
        pattern='^delete_'
    ))

    dp.add_handler(CallbackQueryHandler(
        handle_update_callback,
        pattern='^update_'
    ))

    dp.add_handler(CallbackQueryHandler(
        handle_manual_notification_callback,
        pattern='^manual_send_'
    ))

    # Обработка новой даты события
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command,
        handle_new_date
    ))


def main():
    """Запуск бота"""
    # Загружаем переменные окружения
    load_dotenv()

    # Получаем токен бота
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        logger.error("Не найден токен бота в переменных окружения")
        return

    try:
        # Создаём updater
        updater = Updater(TOKEN, use_context=True)

        # Получаем диспетчер
        dp = updater.dispatcher

        # Регистрируем обработчики
        setup_handlers(dp)

        # Запускаем бота
        updater.start_polling()
        logger.info("✅ Бот успешно запущен")

        # Выводим информацию о боте
        bot_info = updater.bot.get_me()
        logger.info(f"Имя бота: @{bot_info.username}")
        logger.info(f"ID бота: {bot_info.id}")

        # Ожидаем завершения
        updater.idle()

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}", exc_info=True)


from services.notifications.email import EmailNotifier

# Тестирование email настроек
try:
    email_notifier = EmailNotifier()
    if email_notifier.test_connection():
        logger.info("✅ Email настройки корректны")
    else:
        logger.error("❌ Ошибка настроек email")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации email: {str(e)}")

if __name__ == '__main__':
    main()