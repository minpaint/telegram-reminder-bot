from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Укажите путь к вашей базе данных
DATABASE_URL = "sqlite:///data/reminder_bot.db"

# Создание engine
engine = create_engine(DATABASE_URL, echo=True)

# Создание сессии
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()


def delete_event_by_id(event_id):
    try:
        # SQL запрос для удаления строки по event_id
        query = text("DELETE FROM events WHERE event_id = :event_id")

        # Выполнение запроса
        result = session.execute(query, {"event_id": event_id})

        # Коммит изменений
        session.commit()

        if result.rowcount > 0:
            print(f"✅ Событие с ID {event_id} успешно удалено.")
        else:
            print(f"❌ Событие с ID {event_id} не найдено.")
    except Exception as e:
        print(f"❌ Ошибка при удалении события: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    # event_id для удаления
    event_id_to_delete = 18
    delete_event_by_id(event_id_to_delete)
