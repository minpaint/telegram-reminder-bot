import logging
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid

from config.settings import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL

# Настройка логгера
logger = logging.getLogger(__name__)


class EmailNotifier:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.sender_email = SENDER_EMAIL

        # Проверка наличия всех необходимых настроек
        if not all([self.smtp_user, self.smtp_password, self.sender_email]):
            missing_settings = []
            if not self.smtp_user:
                missing_settings.append('SMTP_USER')
            if not self.smtp_password:
                missing_settings.append('SMTP_PASSWORD')
            if not self.sender_email:
                missing_settings.append('SENDER_EMAIL')
            error_msg = f"Missing email settings: {', '.join(missing_settings)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"EmailNotifier initialized with server {self.smtp_server}:{self.smtp_port}")

    def format_text_message(self, event, custom_message=None):
        """Форматирование текстового сообщения"""
        if custom_message:
            return custom_message

        days_left = (event.event_date.date() - datetime.now().date()).days

        message = (
            f"📅 Напоминание о событии\n\n"
            f"📌 Название: {event.event_name}\n"
            f"📆 Дата: {event.event_date.strftime('%d.%m.%Y')}\n"
            f"⏰ До события: {days_left} дней\n"
        )

        if hasattr(event, 'file_name') and event.file_name:
            message += f"📁 Файл: {event.file_name}\n"

        if hasattr(event, 'responsible_telegram_ids') and event.responsible_telegram_ids:
            message += f"👥 Ответственные: {event.responsible_telegram_ids}\n"

        if hasattr(event, 'periodicity') and event.periodicity:
            message += f"🔄 Периодичность: {event.periodicity} мес.\n"

        message += "\n---\nДля отписки от уведомлений ответьте на это письмо с темой 'unsubscribe'"

        return message

    def format_html_message(self, event, custom_message=None):
        """Форматирование HTML сообщения"""
        if custom_message:
            return f"<p>{custom_message}</p>"

        days_left = (event.event_date.date() - datetime.now().date()).days

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
                .header {{ color: #2c3e50; margin-bottom: 20px; }}
                .details {{ margin: 15px 0; background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
                .details p {{ margin: 8px 0; }}
                .footer {{ color: #7f8c8d; font-size: 0.9em; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }}
                .emoji {{ font-size: 1.2em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 class="header"><span class="emoji">📅</span> Напоминание о событии</h2>
                <div class="details">
                    <p><strong>📌 Название:</strong> {event.event_name}</p>
                    <p><strong>📆 Дата:</strong> {event.event_date.strftime('%d.%m.%Y')}</p>
                    <p><strong>⏰ До события:</strong> {days_left} дней</p>
                    {f'<p><strong>📁 Файл:</strong> {event.file_name}</p>' if hasattr(event, 'file_name') and event.file_name else ''}
                    {f'<p><strong>👥 Ответственные:</strong> {event.responsible_telegram_ids}</p>' if hasattr(event, 'responsible_telegram_ids') and event.responsible_telegram_ids else ''}
                    {f'<p><strong>🔄 Периодичность:</strong> {event.periodicity} мес.</p>' if hasattr(event, 'periodicity') and event.periodicity else ''}
                </div>
                <div class="footer">
                    <p>Это автоматическое уведомление от Бота-напоминателя</p>
                    <p>Для отписки от уведомлений ответьте на это письмо с темой "unsubscribe"</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def send_notification(self, db, event, subject=None, message=None):
        """Отправка email уведомления"""
        if not event.responsible_email:
            logger.warning(f"Email не указан для события {event.event_id}")
            return False

        try:
            logger.info(f"Подготовка к отправке email для события {event.event_id} на адрес {event.responsible_email}")

            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("Бот-напоминатель", self.sender_email))
            msg['To'] = event.responsible_email
            msg['Subject'] = subject or f"Напоминание: {event.event_name}"
            msg['Message-ID'] = make_msgid(domain='yandex.ru')
            msg['List-Unsubscribe'] = f'<mailto:{self.sender_email}?subject=unsubscribe>'

            # Создаем текстовую и HTML версии сообщения
            text_part = MIMEText(self.format_text_message(event, message), 'plain', 'utf-8')
            html_part = MIMEText(self.format_html_message(event, message), 'html', 'utf-8')

            # Добавляем обе версии в сообщение
            msg.attach(text_part)
            msg.attach(html_part)

            logger.info(f"Подключение к SMTP серверу {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                logger.debug("Успешная авторизация на SMTP сервере")

                server.send_message(msg)
                logger.info(f"Email успешно отправлен на {event.responsible_email}")
                return True

        except smtplib.SMTPException as smtp_error:
            logger.error(f"SMTP ошибка при отправке email: {str(smtp_error)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Общая ошибка при отправке email: {str(e)}", exc_info=True)
            raise

    def send_multiple_notifications(self, events):
        """Отправка нескольких уведомлений с задержкой"""
        for event in events:
            try:
                self.send_notification(None, event)
                # Добавляем задержку между отправками
                time.sleep(2)
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления для события {event.event_id}: {str(e)}")
                continue

    def test_connection(self):
        """Проверка подключения к SMTP серверу"""
        try:
            logger.info(f"Тестирование подключения к {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                logger.info("Тест подключения успешен")
                return True
        except Exception as e:
            logger.error(f"Ошибка при тестировании подключения: {str(e)}", exc_info=True)
            return False
