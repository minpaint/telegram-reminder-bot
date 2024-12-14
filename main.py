import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from handlers import (
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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def start_command(update, context):
    """Обработчик команды /start."""
    keyboard = [
        ["📋 Мои события", "🔔 Напоминания"],
        ["📂 Добавить файл", "✏️ Изменить событие"],
        ["🗑 Удалить событие"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=reply_markup
    )

def setup_handlers(dp):
    """Регистрация обработчиков"""
    # Команда /start
    dp.add_handler(CommandHandler("start", start_command))

    # Команды через слэш
    dp.add_handler(CommandHandler("my_events", show_events))
    dp.add_handler(CommandHandler("reminders", reminders_command))
    dp.add_handler(CommandHandler("delete_event", delete_event_request))
    dp.add_handler(CommandHandler("update_event", update_event_request))
    dp.add_handler(CommandHandler("add_file", handle_add_file))

    # Текстовые кнопки основного меню
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

    # Обработка файлов
    dp.add_handler(MessageHandler(
        Filters.document.file_extension('xlsx'),
        handle_document
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

def main():
    """Запуск бота"""
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise ValueError("Токен бота отсутствует. Проверьте файл .env")

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
