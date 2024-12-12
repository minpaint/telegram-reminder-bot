import os

# Исправленные пути к файлам
FILES_TO_EDIT = {
    "services/excel/parser.py": [
        {
            "find": "event_date = row[1]",
            "replace": """event_date = row["Дата наступления"]
                   if not isinstance(event_date, datetime):
                       event_date = datetime.strptime(str(event_date), "%Y-%m-%d")"""
        },
        {
            "find": "time_str = str(row[2]).strip().replace(\".\", \":\")",
            "replace": """time_str = str(row["Время наступления"]).strip().replace(".", ":")"""
        },
        {
            "find": "responsible_ids_str = str(row[7]) if pd.notna(row[7]) else \"\"",
            "replace": """responsible_ids_str = str(row["ID ответственных"]) if pd.notna(row["ID ответственных"]) else \"\""""
        },
        {
            "find": "Event.event_name == str(row[0]).strip()",
            "replace": """Event.event_name == str(row["Событие"]).strip()"""
        },
        {
            "find": "logger.error(f\"Ошибка в строке {idx + 2}: {str(e)}\")",
            "replace": """logger.error(f"Ошибка в строке {idx + 2} файла {file_name}: {str(e)}")"""
        }
    ],
    "handlers/files.py": [
        {
            "find": "update.message.reply_text(\"Файл успешно обработан!\")",
            "replace": """update.message.reply_text("Файл успешно обработан!")
       except Exception as e:
           logger.error(f"Ошибка при обработке файла: {str(e)}")
           update.message.reply_text(f"❌ Ошибка при обработке файла: {str(e)}")"""
        }
    ]
}


def edit_file(file_path, changes):
    """
    Редактирует файл, применяя указанные изменения.
    :param file_path: Путь к файлу
    :param changes: Список изменений
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.readlines()

    for change in changes:
        find = change["find"]
        replace = change["replace"]
        for i, line in enumerate(content):
            if find in line:
                content[i] = line.replace(find, replace)
                print(f"Изменение применено в файле {file_path} на строке {i + 1}")
                break
        else:
            print(f"Не найдено изменение для строки '{find}' в файле {file_path}")

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(content)


def main():
    """
    Основная функция для применения изменений ко всем файлам.
    """
    for file_name, changes in FILES_TO_EDIT.items():
        file_path = os.path.join(os.getcwd(), file_name)
        if os.path.exists(file_path):
            print(f"Обработка файла: {file_path}")
            edit_file(file_path, changes)
        else:
            print(f"Файл {file_path} не найден")


if __name__ == "__main__":
    main()