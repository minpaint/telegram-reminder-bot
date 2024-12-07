from telegram.ext import CommandHandler, MessageHandler, Filters


def setup_handlers(dispatcher):
    """Настройка обработчиков команд и сообщений"""
    # Добавьте здесь ваши текущие обработчики
    # Пример:
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Обработчики меню
    menu_handlers = [
        MessageHandler(Filters.regex('^🔔 Напоминания$'), show_reminders),
        MessageHandler(Filters.regex('^📋 Мои события$'), show_events),
        MessageHandler(Filters.regex('^📂 Добавить файл$'), handle_add_file),
    ]

    for handler in menu_handlers:
        dispatcher.add_handler(handler)

    # Обработчик файлов
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))


def start_command(update, context):
    update.message.reply_text(
        "Привет! Я бот для управления напоминаниями.",
        reply_markup=get_base_keyboard()
    )


def help_command(update, context):
    update.message.reply_text(
        "Здесь будет справка по использованию бота"
    )


def show_reminders(update, context):
    update.message.reply_text(
        "Здесь будет список напоминаний"
    )


def show_events(update, context):
    update.message.reply_text(
        "Здесь будет список событий"
    )


def handle_add_file(update, context):
    update.message.reply_text(
        "Загрузите Excel файл с событиями"
    )


def handle_document(update, context):
    update.message.reply_text(
        "Обработка документа"
    )


def get_base_keyboard():
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    keyboard = [
        [KeyboardButton("🔔 Напоминания"), KeyboardButton("📋 Мои события")],
        [KeyboardButton("📂 Добавить файл")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
