import smtplib

# Настройки
smtp_server = "smtp.yandex.ru"
smtp_port = 465
smtp_user = "botnapominatel@yandex.ru"
smtp_password = "c416bf317d03fe7338f86ff1ab35946d"  # ID пароля из скриншота

try:
    # Создаем подключение
    print(f"Подключение к {smtp_server}:{smtp_port}")
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        # Включаем шифрование
        print("Включение TLS")
        server.starttls()

        # Пытаемся залогиниться
        print("Попытка входа...")
        server.login(smtp_user, smtp_password)
        print("Успешное подключение!")

except Exception as e:
    print(f"Ошибка: {str(e)}")
