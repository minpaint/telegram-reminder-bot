from email_validator import validate_email, EmailNotValidError

from core.exceptions import ValidationError


def validate_excel_data(df):
    """Валидация данных из Excel"""
    errors = []

    for index, row in df.iterrows():
        try:
            # Проверка даты
            if pd.isna(row["Дата наступления"]):
                errors.append(f"Строка {index + 2}: Пустая дата")

            # Проверка email
            if not pd.isna(row["Email ответственного"]):
                try:
                    validate_email(row["Email ответственного"])
                except EmailNotValidError:
                    errors.append(f"Строка {index + 2}: Некорректный email")

            # Проверка количества дней для напоминания
            try:
                days = int(row["За сколько дней напомнить"])
                if days < 0:
                    errors.append(f"Строка {index + 2}: Количество дней должно быть положительным")
            except (ValueError, TypeError):
                errors.append(f"Строка {index + 2}: Некорректное количество дней")

        except Exception as e:
            errors.append(f"Строка {index + 2}: {str(e)}")

    if errors:
        raise ValidationError("\n".join(errors))

    return True
