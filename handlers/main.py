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
    handle_new_date
)
from handlers.main import handle_menu_choice

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

    # Обработка callback-запросов для кнопок
    dp.add_handler(CallbackQueryHandler(
        handle_delete_callback,
        pattern='^delete_'
    ))
    dp.add_handler(CallbackQueryHandler(
        handle_update_callback,
        pattern='^update_'
    ))

    # Обработка новой даты события
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command,
        handle_new_date
    ))

    # Общий обработчик текстовых сообщений
    dp.add_handler(MessageHandler(
        Filters.text,
        handle_menu_choice
    ))


def main():
    """Запуск бота"""
    TOKEN = os.getenv("TOKEN")
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер
    dp = updater.dispatcher

    # Регистрируем обработчики
    setup_handlers(dp)

    # Запускаем бота
    updater.start_polling()
    logger.info("Bot started")

    # Ожидаем завершения
    updater.idle()


if __name__ == '__main__':
    load_dotenv()
    main()
