import logging
import os

from telegram import Update
from telegram.ext import CallbackContext

from services.excel.parser import process_excel  # Изменено с process_file на process_excel

# Настройка логирования
logger = logging.getLogger(__name__)


def handle_document(update: Update, context: CallbackContext):
    """Обработчик загруженных файлов"""
    # Проверяем, есть ли документ
    if not update.message.document:
        update.message.reply_text("❌ Файл не найден!")
        return

    file = update.message.document
    # Проверяем формат файла (только .xlsx)
    if not file.file_name.endswith('.xlsx'):
        update.message.reply_text(
            "❌ Неверный формат файла!\n"
            "Пожалуйста, загрузите файл Excel (.xlsx)"
        )
        return

    user_id = update.effective_user.id
    file_name = file.file_name

    try:
        # Создаем временную директорию, если её нет
        os.makedirs('tempfiles', exist_ok=True)
        file_path = f"tempfiles/{file_name}"

        # Скачиваем файл
        file_info = context.bot.get_file(file.file_id)
        file_info.download(file_path)

        # Сообщаем о начале обработки
        update.message.reply_text("📥 Файл получен, начинаю обработку...")

        # Обрабатываем файл с помощью process_excel
        events_created = process_excel(file_path, user_id, file_name)

        # Отправляем результат
        update.message.reply_text(
            f"✅ Файл успешно обработан!\n"
            f"Добавлено событий: {events_created}"
        )

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке файла: {str(e)}")
        update.message.reply_text(
            "❌ Произошла ошибка при обработке файла.\n"
            "Убедитесь, что файл соответствует формату."
        )

    finally:
        # Удаляем временный файл, если он был скачан
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as delete_error:
                logger.error(f"Не удалось удалить временный файл {file_path}: {delete_error}")
