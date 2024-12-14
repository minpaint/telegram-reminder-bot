import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event

logger = logging.getLogger(__name__)

def delete_event_request(update: Update, context: CallbackContext):
    """Запрос на удаление события с инлайн-кнопками"""
    user_id = update.effective_user.id
    logger.info(f"Запрос на удаление события от пользователя {user_id}")

    db = SessionLocal()
    try:
        events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True
        ).all()

        logger.info(f"Найдено {len(events)} событий")

        if not events:
            update.message.reply_text("📭 Нет событий для удаления.")
            return

        events_by_file = {}
        for event in events:
            # Преобразуем дату к datetime с временем по умолчанию
            if isinstance(event.event_date, str):
                try:
                    event.event_date = datetime.strptime(event.event_date, "%Y-%m-%d").replace(hour=0, minute=0,
                                                                                               second=0)
                except ValueError:
                    try:
                        event.event_date = datetime.strptime(event.event_date, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            event.event_date = datetime.strptime(event.event_date, "%d.%m.%Y")
                        except ValueError as e:
                            logger.error(f"Не удалось распарсить дату {event.event_date}, ошибка {e}")
                            continue

            try:
                file_name = event.file_name or "Другие события"
                if file_name not in events_by_file:
                    events_by_file[file_name] = []
                events_by_file[file_name].append(event)
            except Exception as e:
                logger.error(f"Ошибка при обработке события {event.event_id}: {e}")

        keyboard = []

        try:
            if "Другие события" in events_by_file:
                keyboard.append([InlineKeyboardButton("📝 Другие события", callback_data="header_other")])
                for event in sorted(events_by_file["Другие события"], key=lambda x: x.event_date):
                    button_text = f"{event.event_name}: {event.event_date.strftime('%d.%m.%Y')}"
                    callback_data = f"delete_{event.event_id}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                del events_by_file["Другие события"]

            for file_name, file_events in sorted(events_by_file.items()):
                keyboard.append([InlineKeyboardButton(f"📁 {file_name}", callback_data=f"header_{file_name}")])
                for event in sorted(file_events, key=lambda x: x.event_date):
                    button_text = f"{event.event_name}: {event.event_date.strftime('%d.%m.%Y')}"
                    callback_data = f"delete_{event.event_id}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("🗑 Выберите событие для удаления:", reply_markup=reply_markup)
            logger.info("Сообщение отправлено успешно")

        except Exception as e:
            logger.error(f"Ошибка при создании клавиатуры: {e}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Общая ошибка: {e}", exc_info=True)
        update.message.reply_text("❌ Произошла ошибка при получении списка событий")
    finally:
        db.close()

def handle_delete_callback(update: Update, context: CallbackContext):
    """Обработка удаления события"""
    query = update.callback_query
    logger.info(f"Получен callback удаления: {query.data}")
    query.answer()

    if query.data.startswith("header"):
        return

    event_id = int(query.data.split('_')[1])
    logger.info(f"Удаление события {event_id}")

    db = SessionLocal()
    try:
        event = db.query(Event).filter(
            Event.event_id == event_id,
            Event.creator_id == query.from_user.id
        ).first()

        if event:
            event.is_active = False
            db.commit()
            logger.info(f"Событие {event_id} успешно удалено")
            query.edit_message_text("✅ Событие успешно удалено!")
        else:
            logger.warning(f"Событие {event_id} не найдено")
            query.edit_message_text("❌ Событие не найдено.")
    finally:
        db.close()

def update_event_request(update: Update, context: CallbackContext):
    """Запрос на обновление события с инлайн-кнопками"""
    user_id = update.effective_user.id
    logger.info(f"Запрос на обновление события от пользователя {user_id}")

    db = SessionLocal()
    try:
        events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True
        ).order_by(Event.file_name, Event.event_date).all()

        logger.info(f"Найдено {len(events)} событий")

        if not events:
            update.message.reply_text("📭 У вас нет активных событий.")
            return

        events_by_file = {}
        for event in events:
            try:
                file_name = event.file_name or "Другие события"
                if file_name not in events_by_file:
                    events_by_file[file_name] = []
                events_by_file[file_name].append(event)
            except Exception as e:
                logger.error(f"Ошибка при обработке события {event.event_id}: {e}")

        keyboard = []

        try:
            if "Другие события" in events_by_file:
                keyboard.append([InlineKeyboardButton("📝 Другие события", callback_data="header_other")])
                for event in sorted(events_by_file["Другие события"], key=lambda x: x.event_date):
                    button_text = f"{event.event_name}: {event.event_date.strftime('%d.%m.%Y')}"
                    callback_data = f"update_{event.event_id}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                del events_by_file["Другие события"]

            for file_name, file_events in sorted(events_by_file.items()):
                keyboard.append([InlineKeyboardButton(f"📁 {file_name}", callback_data=f"header_{file_name}")])
                for event in sorted(file_events, key=lambda x: x.event_date):
                    button_text = f"{event.event_name}: {event.event_date.strftime('%d.%m.%Y')}"
                    callback_data = f"update_{event.event_id}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("✏️ Выберите событие для изменения:", reply_markup=reply_markup)
            logger.info("Сообщение отправлено успешно")

        except Exception as e:
            logger.error(f"Ошибка при создании клавиатуры: {e}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Общая ошибка: {e}", exc_info=True)
        update.message.reply_text("❌ Произошла ошибка при получении списка событий")
    finally:
        db.close()

def handle_update_callback(update: Update, context: CallbackContext):
    """Обработка выбора события для обновления"""
    query = update.callback_query
    logger.info(f"Получен callback обновления: {query.data}")
    query.answer()

    if query.data.startswith("header"):
        return

    try:
        event_id = int(query.data.split('_')[1])
        logger.info(f"Обновление события {event_id}")

        # Сохраняем ID события для последующего обновления
        context.user_data['updating_event'] = event_id

        # Получаем информацию о событии
        db = SessionLocal()
        try:
            event = db.query(Event).filter(
                Event.event_id == event_id,
                Event.creator_id == query.from_user.id
            ).first()

            if event:
                message = (
                    f"🔄 Обновление события:\n"
                    f"Название: {event.event_name}\n"
                    f"Текущая дата: {event.event_date.strftime('%d.%m.%Y')}\n\n"
                    f"📅 Введите новую дату события в формате ДД.ММ.ГГГГ"
                )
                query.edit_message_text(text=message)
            else:
                query.edit_message_text(text="❌ Событие не найдено")

        except Exception as e:
            logger.error(f"Ошибка при получении события: {e}", exc_info=True)
            query.edit_message_text(text="❌ Произошла ошибка при обновлении события")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Ошибка при обработке callback обновления: {e}", exc_info=True)
        query.edit_message_text(text="❌ Произошла ошибка при обновлении события")

def handle_new_date(update: Update, context: CallbackContext):
    """Обработка новой даты события"""
    if 'updating_event' not in context.user_data:
        return  # Пропускаем обработку, если это не обновление даты

    try:
        new_date = datetime.strptime(update.message.text.strip(), "%d.%m.%Y")
        event_id = context.user_data['updating_event']
        logger.info(f"Попытка обновления даты события {event_id} на {new_date}")

        db = SessionLocal()
        try:
            event = db.query(Event).filter(
                Event.event_id == event_id,
                Event.creator_id == update.effective_user.id
            ).first()

            if event:
                old_date = event.event_date
                event.event_date = new_date
                try:
                    db.commit()
                    logger.info(f"Дата события {event_id} успешно обновлена")

                    message = (
                        f"✅ Дата события '{event.event_name}' изменена!\n"
                        f"Старая дата: {old_date.strftime('%d.%m.%Y')}\n"
                        f"Новая дата: {new_date.strftime('%d.%m.%Y')}"
                    )
                    update.message.reply_text(message)
                except Exception as commit_error:
                    logger.error(f"Ошибка при сохранении изменений: {commit_error}", exc_info=True)
                    db.rollback()
                    update.message.reply_text("❌ Ошибка при сохранении изменений")
            else:
                logger.warning(f"Событие {event_id} не найдено")
                update.message.reply_text("❌ Событие не найдено")
        finally:
            db.close()

    except ValueError:
        logger.error("Ошибка формата даты")
        update.message.reply_text(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ"
        )
    finally:
        if 'updating_event' in context.user_data:
            del context.user_data['updating_event']
