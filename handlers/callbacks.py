from telegram import Update
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event


def handle_delete_callback(update: Update, context: CallbackContext):
    """Обработчик callback для удаления события"""
    query = update.callback_query
    user_id = query.from_user.id
    event_id = int(query.data.split('_')[1])

    db = SessionLocal()
    try:
        event = db.query(Event).filter(
            Event.id == event_id,
            Event.creator_id == user_id
        ).first()

        if not event:
            query.answer("❌ Событие не найдено")
            return

        event.is_active = False
        db.commit()
        query.answer("✅ Событие успешно удалено")
        query.edit_message_text("Событие удалено")

    except Exception as e:
        query.answer(f"❌ Ошибка: {str(e)}")
    finally:
        db.close()


def handle_update_callback(update: Update, context: CallbackContext):
    """Обработчик callback для обновления события"""
    query = update.callback_query
    user_id = query.from_user.id
    event_id = int(query.data.split('_')[1])

    db = SessionLocal()
    try:
        event = db.query(Event).filter(
            Event.id == event_id,
            Event.creator_id == user_id
        ).first()

        if not event:
            query.answer("❌ Событие не найдено")
            return

        context.user_data['event_to_update'] = event_id
        query.answer("✅ Выберите новую дату события (ДД.ММ.ГГГГ)")
        query.edit_message_text(
            "Введите новую дату события в формате ДД.ММ.ГГГГ\n"
            "Например: 25.12.2024"
        )

    except Exception as e:
        query.answer(f"❌ Ошибка: {str(e)}")
    finally:
        db.close()
