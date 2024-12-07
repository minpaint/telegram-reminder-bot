import logging
import os
from datetime import datetime, timedelta

import pandas as pd

from core.database import SessionLocal
from models import Event

logger = logging.getLogger(__name__)


def process_excel(file_path, user_id, file_name):
    """Обработка Excel файла"""
    try:
        logger.info(f"Начало обработки файла: {file_path}")

        # Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            raise ValueError("Файл не найден")

        # Читаем Excel файл
        df = pd.read_excel(file_path)
        logger.info(f"Файл прочитан успешно, строк: {len(df)}")

        # Проверяем обязательные колонки
        required_columns = [
            "Событие",
            "Дата наступления",
            "Время наступления",
            "За сколько дней напомнить",
            "Повтор события",
            "Периодичность (мес)",
            "Ответственный",
            "Email ответственного"
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"В файле отсутствуют колонки: {', '.join(missing_columns)}")

        events_created = 0
        db = SessionLocal()
        try:
            for idx, row in df.iterrows():
                logger.info(f"Обработка строки {idx + 2}")
                try:
                    # Конвертируем дату в нужный формат
                    date_str = str(row["Дата наступления"])
                    if isinstance(row["Дата наступления"], pd.Timestamp):
                        event_date = row["Дата наступления"].to_pydatetime()
                    else:
                        event_date = datetime.strptime(date_str, "%d.%m.%Y")

                    # Обработка времени
                    time_str = str(row["Время наступления"]).strip().replace(".", ":")
                    event_time = datetime.strptime(time_str, "%H:%M").time()

                    # Создаем событие
                    event = Event(
                        creator_id=user_id,
                        file_name=file_name,
                        event_name=str(row["Событие"]).strip(),
                        event_date=event_date.date(),  # Берем только дату
                        event_time=event_time,
                        remind_before=int(row["За сколько дней напомнить"]),
                        repeat_type=str(row["Повтор события"]).strip(),
                        periodicity=int(row["Периодичность (мес)"]) if pd.notna(row["Периодичность (мес)"]) else 0,
                        responsible_username=str(row["Ответственный"]).strip(),
                        responsible_email=str(row["Email ответственного"]).strip(),
                        is_active=True
                    )

                    # Устанавливаем дату напоминания
                    remind_date = event_date - timedelta(days=int(row["За сколько дней напомнить"]))
                    event.next_reminder = datetime.combine(remind_date.date(), event_time)

                    db.add(event)
                    events_created += 1
                    logger.info(f"Событие '{event.event_name}' добавлено")

                except Exception as e:
                    logger.error(f"Ошибка в строке {idx + 2}: {str(e)}")
                    raise ValueError(f"Ошибка в строке {idx + 2}: {str(e)}")

            db.commit()
            logger.info(f"Обработка завершена, создано событий: {events_created}")
            return events_created

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при создании события: {str(e)}")
            raise
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Ошибка обработки файла: {str(e)}")
        raise ValueError(f"Ошибка обработки файла: {str(e)}")
