from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_URL
from models import Event


def delete_event(event_id):
    """Удаляет событие из базы данных по event_id."""
    # Создаем движок SQLAlchemy
    engine = create_engine(DATABASE_URL)
    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Находим событие по event_id
        event_to_delete = session.query(Event).filter(Event.event_id == event_id).first()

        if event_to_delete:
            # Преобразовываем event_date если это строка
            if isinstance(event_to_delete.event_date, str):
                try:
                    event_to_delete.event_date = datetime.strptime(event_to_delete.event_date, "%Y-%m-%d")
                except ValueError:
                    try:
                        event_to_delete.event_date = datetime.strptime(event_to_delete.event_date, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        event_to_delete.event_date = datetime.strptime(event_to_delete.event_date, "%d.%m.%Y")
            # Удаляем событие
            session.delete(event_to_delete)
            session.commit()
            print(f"Событие с event_id {event_id} успешно удалено.")
        else:
            print(f"Событие с event_id {event_id} не найдено.")
    except Exception as e:
        session.rollback()
        print(f"Произошла ошибка при удалении события: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    event_id_to_delete = 1
    delete_event(event_id_to_delete)
