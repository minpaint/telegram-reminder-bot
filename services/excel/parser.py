import logging
import os
from datetime import datetime, timedelta, time

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

        # Читаем Excel файл, прося pandas читать все как текст
        df = pd.read_excel(file_path, header=None, dtype=str)
        logger.info(f"Файл прочитан успешно, строк: {len(df)}")

        # Порядок колонок (индексы начинаются с 0)
        column_order = {
            0: "Событие",
            1: "Дата наступления",
            2: "Время наступления",
            3: "За сколько дней напомнить",
            4: "Повтор события",
            5: "Периодичность (мес)",
            6: "Email ответственного",
            7: "ID ответственных"
        }

        events_created = 0
        events_updated = 0
        db = SessionLocal()
        try:
            for idx, row in df.iterrows():
                if idx == 0:  # Пропускаем первую строку (заголовки)
                    continue

                logger.info(f"Обработка строки {idx + 1}")
                try:
                    # Обработка даты
                    date_str = str(row.iloc[1]).strip()
                    try:
                        event_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")  # пробуем сначала такой формат
                    except ValueError:
                        try:
                            event_date = datetime.strptime(date_str, "%d.%m.%Y")  # попробуем такой формат
                        except ValueError:
                            try:
                                event_date = datetime.strptime(date_str, "%Y-%m-%d")  # попробуем еще такой формат
                            except ValueError:
                                try:
                                    event_date = datetime.strptime(date_str, "%Y-%m-%d")
                                except ValueError:
                                    raise ValueError(f"Не удалось распарсить дату: {date_str}")

                    # Обработка времени
                    time_str = str(row.iloc[2]).strip().replace(".", ":")
                    logger.info(f"time_str value: {time_str}")  # Log value before parsing
                    if pd.isna(time_str) or time_str.strip() == "":
                        event_time = time(9, 0)  # set default time
                        logger.info(f"default event_time value: {event_time}, type: {type(event_time)}")
                    else:
                        try:
                            time_str = str(time_str)
                            event_time = datetime.strptime(time_str, "%H:%M").time()
                        except ValueError:
                            try:
                                event_time = datetime.strptime(time_str, "%H:%M:%S").time()
                            except ValueError:
                                raise ValueError(f"Некорректный формат времени: {time_str}")

                    # Обработка списка Telegram ID
                    responsible_ids_str = str(row.iloc[7]) if pd.notna(row.iloc[7]) else ""
                    responsible_ids = [int(single_id.strip()) for single_id in responsible_ids_str.split(",") if
                                       single_id.strip()]
                    responsible_telegram_ids = ",".join(map(str, responsible_ids))

                    # Проверяем, существует ли событие
                    existing_event = db.query(Event).filter(
                        Event.file_name == file_name,
                        Event.event_name == str(row.iloc[0]).strip()
                    ).first()

                    if existing_event:
                        # Обновляем существующее событие
                        existing_event.event_date = event_date
                        existing_event.event_time = event_time
                        existing_event.remind_before = int(row.iloc[3])
                        try:
                            existing_event.periodicity = int(row.iloc[5]) if pd.notna(row.iloc[5]) else 0
                        except ValueError:
                            existing_event.periodicity = 0
                        existing_event.repeat_type = str(row.iloc[4]).strip()
                        existing_event.responsible_email = str(row.iloc[6]).strip()
                        existing_event.responsible_telegram_ids = responsible_telegram_ids
                        # Устанавливаем дату напоминания
                        remind_date = event_date - timedelta(days=int(row.iloc[3]))
                        existing_event.next_reminder = datetime.combine(remind_date.date(), event_time)

                        events_updated += 1
                        logger.info(f"Событие '{existing_event.event_name}' обновлено")
                    else:
                        # Создаем новое событие
                        try:
                            periodicity = int(row.iloc[5]) if pd.notna(row.iloc[5]) else 0
                        except ValueError:
                            periodicity = 0

                        event = Event(
                            creator_id=user_id,
                            file_name=file_name,
                            event_name=str(row.iloc[0]).strip(),
                            event_date=event_date.date(),
                            event_time=event_time,
                            remind_before=int(row.iloc[3]),
                            repeat_type=str(row.iloc[4]).strip(),
                            periodicity=periodicity,
                            responsible_email=str(row.iloc[6]).strip(),
                            responsible_telegram_ids=responsible_telegram_ids,
                            is_active=True
                        )
                        # Устанавливаем дату напоминания
                        remind_date = event_date - timedelta(days=int(row.iloc[3]))
                        event.next_reminder = datetime.combine(remind_date.date(), event_time)

                        db.add(event)
                        events_created += 1
                        logger.info(f"Событие '{event.event_name}' добавлено")

                except Exception as e:
                    logger.error(f"Ошибка в строке {idx + 1}: {str(e)}")
                    raise ValueError(f"Ошибка в строке {idx + 1}: {str(e)}")

            db.commit()
            logger.info(f"Обработка завершена, создано событий: {events_created}, обновлено событий: {events_updated}")
            return events_created, events_updated

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при создании/обновлении события: {str(e)}")
            raise
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Ошибка обработки файла: {str(e)}")
        raise ValueError(f"Ошибка обработки файла: {str(e)}")