import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
from models.notification import Notification, NotificationType, NotificationStatus

logger = logging.getLogger(__name__)


class EmailNotifier:
    def format_message(self, event):
        """Форматирование HTML сообщения"""
        days_left = (event.event_date - datetime.now()).days

        html = f"""
        <html>
            <body>
                <h2>Напоминание о событии</h2>
                <p><strong>Событие:</strong> {event.event_name}</p>
                <p><strong>Дата:</strong> {event.event_date.strftime('%d.%m.%Y')}</p>
                <p><strong>До события:</strong> {days_left} дней</p>
        """

        if event.periodicity:
            html += f"<p><strong>Периодичность:</strong> {event.periodicity} мес.</p>"

        html += """
            <hr>
            <p><small>Это автоматическое уведомление, пожалуйста, не отвечайте на него.</small></p>
            </body>
        </html>
        """

        return html

    def send_notification(self, db, event):
        """Отправка уведомления по email"""
        if not event.responsible_email:
            return

        try:
            # Создаем запись об уведомлении
            notification = Notification(
                event_id=event.event_id,
                user_id=event.creator_id,  # используем creator_id для связи
                type=NotificationType.EMAIL,
                scheduled_at=datetime.now()
            )

            # Формируем email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Напоминание: {event.event_name}"
            msg['From'] = SMTP_USERNAME
            msg['To'] = event.responsible_email

            html_content = self.format_message(event)
            msg.attach(MIMEText(html_content, 'html'))

            # Отправляем email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

            # Обновляем статус
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now()

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            if notification:
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(e)

        finally:
            if notification:
                db.add(notification)
                db.commit()