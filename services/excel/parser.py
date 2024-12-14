import logging
import os
from datetime import datetime, timedelta

import pandas as pd

from core.database import SessionLocal
from models import Event

logger = logging.getLogger(__name__)


def validate_row(row, idx):
    """Валидация строки данных."""
    errors = []

    # Проверка на наличие обязательных полей
    if pd.isna(row.iloc[0]) or not str(row.iloc[0]).strip():
        errors.append(f"Строка {idx + 1}: Поле 'Событие' не должно быть пустым")

    if pd.isna(row.iloc[1]) or not str(row.iloc[1]).strip():
        errors.append(f"Строка {idx + 1}: Поле 'Дата наступления' не должно быть пустым")

    if pd.isna(row.iloc[2]) or not str(row.iloc[2]).strip().isdigit():
        errors.append(f"Строка {idx + 1}: Поле 'За сколько дней напомнить' должно быть числом")

    # Проверка даты
    try:
        date_str = str(row.iloc[1]).strip()
        datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                datetime.strptime(date_str, "%d.%m.%Y")
            except ValueError:
                errors.append(f"Строка {idx + 1}: Некорректный формат даты '{date_str}'")

    return errors


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
            2: "За сколько дней напомнить",
            3: "Повтор события",
            4: "Периодичность (мес)",
            5: "Email ответственного",
            6: "ID ответственных"
        }

        events_created = 0
        events_updated = 0
        db = SessionLocal()
        try:
            for idx, row in df.iterrows():
                if idx == 0:  # Пропускаем первую строку (заголовки)
                    continue

                logger.info(f"Обработка строки {idx + 1}")
                logger.debug(f"Данные строки {idx + 1}: {row.to_dict()}")  # Логируем данные строки

                # Валидация строки
                errors = validate_row(row, idx)
                if errors:
                    for error in errors:
                        logger.error(error)
                    continue

                try:
                    # Обработка даты
                    date_str = str(row.iloc[1]).strip()
                    try:
                        event_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            event_date = datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            event_date = datetime.strptime(date_str, "%d.%m.%Y")

                    # Проверка значения "Периодичность"
                    periodicity_value = row.iloc[4]
                    if pd.isna(periodicity_value) or str(periodicity_value).strip().lower() == "нет":
                        periodicity = 0
                    else:
                        try:
                            periodicity = int(periodicity_value)
                        except ValueError:
                            logger.error(
                                f"Строка {idx + 1}: Некорректное значение периодичности '{periodicity_value}', установлено значение 0")
                            periodicity = 0

                    # Проверяем, существует ли событие
                    existing_event = db.query(Event).filter(
                        Event.file_name == file_name,
                        Event.event_name == str(row.iloc[0]).strip()
                    ).first()

                    if existing_event:
                        # Обновляем существующее событие
                        existing_event.event_date = event_date
                        existing_event.remind_before = int(row.iloc[2])
                        existing_event.periodicity = periodicity
                        existing_event.repeat_type = str(row.iloc[3]).strip()
                        existing_event.responsible_email = str(row.iloc[5]).strip()

                        # Устанавливаем дату напоминания
                        remind_date = event_date - timedelta(days=int(row.iloc[2]))
                        existing_event.next_reminder = remind_date

                        events_updated += 1
                        logger.info(f"Событие '{existing_event.event_name}' обновлено")
                    else:
                        # Создаем новое событие
                        event = Event(
                            creator_id=user_id,
                            file_name=file_name,
                            event_name=str(row.iloc[0]).strip(),
                            event_date=event_date,
                            remind_before=int(row.iloc[2]),
                            repeat_type=str(row.iloc[3]).strip(),
                            periodicity=periodicity,
                            responsible_email=str(row.iloc[5]).strip(),
                            is_active=True,
                        )

                        # Устанавливаем дату напоминания
                        remind_date = event_date - timedelta(days=int(row.iloc[2]))
                        event.next_reminder = remind_date

                        db.add(event)
                        events_created += 1
                        logger.info(f"Событие '{event.event_name}' добавлено")

                except Exception as e:
                    logger.error(f"Ошибка в строке {idx + 1}: {str(e)}")
                    continue

            db.commit()
            logger.info(
                f"Обработка завершена, создано событий: {events_created}, обновлено событий: {events_updated}")
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