from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from .commands import start_command, help_command, stats_command
from .events import (
    show_events, delete_event_request, handle_delete_callback,
    update_event_request
)
from .files import handle_document


def setup_handlers(dispatcher):
    """Настройка всех обработчиков"""

    # Команды
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("stats", stats_command))

    # Обработчики меню
    dispatcher.add_handler(MessageHandler(
        Filters.regex('^📋 Мои события$'),
        show_events
    ))
    dispatcher.add_handler(MessageHandler(
        Filters.regex('^🗑 Удалить событие$'),
        delete_event_request
    ))
    dispatcher.add_handler(MessageHandler(
        Filters.regex('^✏️ Изменить событие$'),
        update_event_request
    ))

    # Обработчик файлов
    dispatcher.add_handler(MessageHandler(
        Filters.document,
        handle_document
    ))

    # Обработчики callback-запросов
    dispatcher.add_handler(CallbackQueryHandler(
        handle_delete_callback,
        pattern='^del_'
    ))
