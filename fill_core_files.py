def modify_file(file_path, modifications):
    """Изменяет файл, применяя список модификаций."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        modified_lines = lines[:]
        for old, new in modifications:
            for i, line in enumerate(modified_lines):
                if old in line:
                    modified_lines[i] = line.replace(old, new)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(modified_lines)
        print(f"Файл {file_path} успешно изменен.")

    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
    except Exception as e:
        print(f"Ошибка при изменении файла {file_path}: {e}")


def remove_lines(file_path, lines_to_remove):
    """Удаляет строки из файла, если они соответствуют списку строк."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        modified_lines = [line for line in lines if not any(remove_line in line for remove_line in lines_to_remove)]

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(modified_lines)
        print(f"Файл {file_path} успешно изменен.")

    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
    except Exception as e:
        print(f"Ошибка при изменении файла {file_path}: {e}")


def main():
    """Главная функция, которая выполняет изменения."""

    # 1 Изменить `handlers/base.py`
    base_file = r'd:\YandexDisk\telegram_reminder_bot\handlers\base.py'
    modifications = [
        (
        '    keyboard = [\n        [KeyboardButton("🔔 Напоминания"), KeyboardButton("📋 Мои события")],\n        [KeyboardButton("📂 Добавить файл"), KeyboardButton("✏️ Изменить событие")],\n        [KeyboardButton("🗑 Удалить событие"), KeyboardButton("🔄 Перезапустить")]\n    ]\n',
        '    keyboard = [\n        [KeyboardButton("🔔 Напоминания"), KeyboardButton("📋 Мои события")],\n        [KeyboardButton("📂 Добавить файл"), KeyboardButton("✏️ Изменить событие")],\n        [KeyboardButton("🗑 Удалить событие")]\n    ]\n')
    ]
    modify_file(base_file, modifications)
    # 2 Изменить `main.py`
    main_file = r'd:\YandexDisk\telegram_reminder_bot\main.py'
    lines_to_remove = [
        'from handlers.commands import handle_menu_choice',
        '    # Общий обработчик текстовых сообщений\n    dp.add_handler(MessageHandler(\n        Filters.text,\n        handle_menu_choice\n    ))'
    ]
    remove_lines(main_file, lines_to_remove)
    # 3 Изменить `handlers/commands.py`
    commands_file = r'd:\YandexDisk\telegram_reminder_bot\handlers\commands.py'
    lines_to_remove_commands = [
        'def handle_menu_choice(update: Update, context: CallbackContext):\n    """Обработка выбора в меню"""\n    text = update.message.text\n\n    if text == "📂 Добавить файл":\n        handle_add_file(update, context)\n    elif text == "🔔 Напоминания":\n        reminders_command(update, context)\n    elif text == "📋 Мои события":\n        show_events(update, context)\n    elif text == "✏️ Изменить событие":\n        update_event_request(update, context)\n    elif text == "🗑 Удалить событие":\n        delete_event_request(update, context)\n    elif text == "🔄 Перезапустить":\n        restart_command(update, context)',
        'def restart_command(update: Update, context: CallbackContext):\n    """Перезапуск бота"""\n    user_id = update.effective_user.id\n    message = "🔄 Бот перезапущен."\n    keyboard = get_base_keyboard(user_id)\n    update.message.reply_text(message, reply_markup=keyboard)'
    ]
    remove_lines(commands_file, lines_to_remove_commands)
    # 4 Изменить `handlers/main.py`
    main_file = r'd:\YandexDisk\telegram_reminder_bot\handlers\main.py'
    modifications_main = [
        ("from handlers.commands import start_command, help_command, stats_command, handle_menu_choice",
         "from handlers.commands import start_command, stats_command, handle_menu_choice, handle_add_file"),
        ("    dispatcher.add_handler(CommandHandler(\"help\", help_command))", ""),
    ]
    modify_file(main_file, modifications_main)
    lines_to_remove_main = [
        'from handlers.commands import help_command'
    ]
    remove_lines(main_file, lines_to_remove_main)
    # 5 Изменить `handlers/__init__.py`
    init_file = r'd:\YandexDisk\telegram_reminder_bot\handlers\__init__.py'
    lines_to_remove_init = [
        '    handle_menu_choice\n'
    ]
    remove_lines(init_file, lines_to_remove_init)

    modifications_init = [
        (
        "from .commands import (\n    start_command,\n    show_events,\n    reminders_command,\n    handle_add_file,\n    handle_menu_choice\n)",
        "from .commands import (\n    start_command,\n    show_events,\n    reminders_command,\n    handle_add_file,\n)"),
    ]
    modify_file(init_file, modifications_init)

    print("Все изменения успешно выполнены.")

if __name__ == "__main__":
    main()
