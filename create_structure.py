import os
import re


def fix_main_py(file_path):
    """Исправляет main.py"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Удаляем handle_new_date из импорта
    content = re.sub(
        r'from handlers\.commands import (.+), handle_new_date(.+)',
        r'from handlers.commands import \1\2',
        content
    )

    # Удаляем блок обработчика handle_new_date
    content = re.sub(
        r'\s*# Обработка ввода новой даты\s*dp\.add_handler$MessageHandler\(\s*Filters\.regex\(r\'\^\\\d{2}\.\\\d{2}\.\\\d{4}\$\'$,\s*handle_new_date\s*\)\)',
        '',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


def fix_init_py(file_path):
    """Исправляет __init__.py"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Удаляем handle_new_date из импорта
    content = re.sub(
        r'from \.commands import (.+), handle_new_date(.+)',
        r'from .commands import \1\2',
        content
    )

    # Удаляем handle_new_date из __all__
    content = re.sub(
        r"'handle_new_date',\s*",
        '',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


def fix_commands_py(file_path):
    """Исправляет commands.py"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Удаляем всю функцию handle_new_date
    content = re.sub(
        r'\ndef handle_new_date$update: Update, context: CallbackContext$:[\s\S]*?(?=\ndef|$)',
        '\n',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


def main():
    # Пути к файлам
    base_path = os.getcwd()  # Текущая директория
    main_path = os.path.join(base_path, 'main.py')
    init_path = os.path.join(base_path, 'handlers', '__init__.py')
    commands_path = os.path.join(base_path, 'handlers', 'commands.py')

    # Проверяем существование файлов
    files_to_check = [
        (main_path, 'main.py'),
        (init_path, 'handlers/__init__.py'),
        (commands_path, 'handlers/commands.py')
    ]

    for file_path, file_name in files_to_check:
        if not os.path.exists(file_path):
            print(f"Ошибка: файл {file_name} не найден")
            return

    try:
        # Создаем резервные копии
        for file_path, file_name in files_to_check:
            backup_path = file_path + '.backup'
            with open(file_path, 'r', encoding='utf-8') as source:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(source.read())
            print(f"Создана резервная копия {file_name}")

        # Вносим изменения
        fix_main_py(main_path)
        fix_init_py(init_path)
        fix_commands_py(commands_path)

        print("\nВсе изменения успешно внесены!")
        print("Резервные копии файлов созданы с расширением .backup")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        print("Попробуйте восстановить файлы из резервных копий (.backup)")


if __name__ == "__main__":
    main()
