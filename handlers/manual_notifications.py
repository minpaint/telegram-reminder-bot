import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from core.database import SessionLocal
from models import Event, Notification, NotificationStatus, NotificationType
from services.notifications.email import EmailNotifier

logger = logging.getLogger(__name__)


def manual_notification_request(update: Update, context: CallbackContext):
    """Запрос на ручную отправку напоминаний"""
    user_id = update.effective_user.id
    logger.info(f"Запрос на ручную отправку напоминания от пользователя {user_id}")

    db = SessionLocal()
    try:
        events = db.query(Event).filter(
            Event.creator_id == user_id,
            Event.is_active == True
        ).order_by(Event.file_name, Event.event_date).all()

        if not events:
            update.message.reply_text("📭 У вас нет активных событий для отправки напоминаний.")
            return

        events_by_file = {}
        for event in events:
            file_name = event.file_name or "Другие события"
            if file_name not in events_by_file:
                events_by_file[file_name] = []
            events_by_file[file_name].append(event)

        keyboard = []
        if "Другие события" in events_by_file:
            keyboard.append([InlineKeyboardButton("📝 Другие события", callback_data="header_other")])
            for event in sorted(events_by_file["Другие события"], key=lambda x: x.event_date):
                button_text = f"{event.event_name} ({event.event_date.strftime('%d.%m.%Y')})"
                keyboard.append([
                    InlineKeyboardButton(
                        f"📢 {button_text}",
                        callback_data=f"manual_send_{event.event_id}"
                    )
                ])
            del events_by_file["Другие события"]

        for file_name, file_events in sorted(events_by_file.items()):
            keyboard.append([InlineKeyboardButton(f"📁 {file_name}", callback_data=f"header_{file_name}")])
            for event in sorted(file_events, key=lambda x: x.event_date):
                button_text = f"{event.event_name} ({event.event_date.strftime('%d.%m.%Y')})"
                keyboard.append([
                    InlineKeyboardButton(
                        f"📢 {button_text}",
                        callback_data=f"manual_send_{event.event_id}"
                    )
                ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "📢 Выберите событие для отправки напоминания:\n"
            "⚠️ Напоминание будет отправлено всем ответственным лицам",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Ошибка при формировании списка событий: {e}", exc_info=True)
        update.message.reply_text("❌ Произошла ошибка при получении списка событий")
    finally:
        db.close()


def handle_manual_notification_callback(update: Update, context: CallbackContext):
    """Обработка отправки ручного напоминания"""
    query = update.callback_query
    logger.info(f"Получен callback: {query.data}")

    query.answer()

    if query.data.startswith("header_"):
        logger.info("Это заголовок, пропускаем обработку")
        return

    try:
        event_id = int(query.data.split('_')[-1])
        user_id = query.from_user.id
        logger.info(f"Обработка события {event_id} для пользователя {user_id}")

        db = SessionLocal()
        try:
            event = db.query(Event).filter(
                Event.event_id == event_id,
                Event.creator_id == user_id,
                Event.is_active == True
            ).first()

            if not event:
                logger.warning(f"Событие {event_id} не найдено")
                query.edit_message_text("❌ Событие не найдено или было удалено")
                return

            logger.info(f"Событие найдено: {event.event_name}")
            logger.info(f"Ответственные: {event.responsible_telegram_ids}")

            try:
                test_message = "🔔 Тестовое сообщение от бота"
                context.bot.send_message(
                    chat_id=user_id,
                    text=test_message
                )
                logger.info("Тестовое сообщение отправлено успешно")
            except Exception as e:
                logger.error(f"Ошибка отправки тестового сообщения: {str(e)}")

            days_left = (event.event_date.date() - datetime.now().date()).days
            message = (
                f"🔔 <b>Ручное напоминание о событии</b>\n\n"
                f"📌 Событие: {event.event_name}\n"
                f"📅 Дата: {event.event_date.strftime('%d.%m.%Y')}\n"
                f"⏰ До события: {days_left} дней\n"
                f"🕒 Время отправки: {datetime.now().strftime('%H:%M:%S')}\n"
                f"👤 Отправитель: {user_id}\n"
            )

            if event.responsible_telegram_ids:
                message += f"📋 Ответственные: {event.responsible_telegram_ids}\n"
            if event.responsible_email:
                message += f"📧 Email: {event.responsible_email}\n"

            success_telegram = False
            success_email = False

            if event.responsible_telegram_ids:
                telegram_ids = event.responsible_telegram_ids.split(',')
                logger.info(f"Список ID для отправки в Telegram: {telegram_ids}")

                for telegram_id in telegram_ids:
                    telegram_id = telegram_id.strip()
                    try:
                        if not telegram_id:
                            logger.warning("Пустой telegram_id, пропускаем")
                            continue

                        logger.info(f"Попытка отправки сообщения в Telegram пользователю {telegram_id}")
                        context.bot.send_message(
                            chat_id=telegram_id,
                            text=message,
                            parse_mode='HTML'
                        )
                        success_telegram = True
                        logger.info(f"Сообщение успешно отправлено в Telegram пользователю {telegram_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки в Telegram {telegram_id}: {str(e)}")

            if event.responsible_email:
                try:
                    logger.info(f"Попытка отправки на email: {event.responsible_email}")
                    email_notifier = EmailNotifier()
                    email_message = (
                        f"Напоминание о событии\n\n"
                        f"Событие: {event.event_name}\n"
                        f"Дата: {event.event_date.strftime('%d.%m.%Y')}\n"
                        f"До события: {days_left} дней\n"
                    )
                    if event.responsible_telegram_ids:
                        email_message += f"Ответственные: {event.responsible_telegram_ids}\n"

                    email_notifier.send_notification(
                        db=db,
                        event=event,
                        subject=f"Напоминание: {event.event_name}",
                        message=email_message
                    )
                    success_email = True
                    logger.info(f"Email успешно отправлен на {event.responsible_email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки email: {str(e)}", exc_info=True)

            if event.responsible_telegram_ids:
                notification_telegram = Notification(
                    event_id=event.event_id,
                    user_id=user_id,
                    type=NotificationType.TELEGRAM,
                    status=NotificationStatus.SENT if success_telegram else NotificationStatus.FAILED,
                    scheduled_at=datetime.now(),
                    sent_at=datetime.now() if success_telegram else None
                )
                db.add(notification_telegram)

            if event.responsible_email:
                notification_email = Notification(
                    event_id=event.event_id,
                    user_id=user_id,
                    type=NotificationType.EMAIL,
                    status=NotificationStatus.SENT if success_email else NotificationStatus.FAILED,
                    scheduled_at=datetime.now(),
                    sent_at=datetime.now() if success_email else None
                )
                db.add(notification_email)

            db.commit()

            status_message = "📤 Статус отправки напоминаний:\n\n"

            if event.responsible_telegram_ids:
                status = "✅" if success_telegram else "❌"
                status_message += f"{status} Telegram\n"

            if event.responsible_email:
                status = "✅" if success_email else "❌"
                status_message += f"{status} Email ({event.responsible_email})\n"

            query.edit_message_text(status_message)
            logger.info(
                f"Напоминание для события {event_id} обработано. Telegram: {success_telegram}, Email: {success_email}")

        except Exception as db_error:
            logger.error(f"Ошибка работы с БД: {db_error}", exc_info=True)
            query.edit_message_text("❌ Ошибка при обработке запроса")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Общая ошибка обработки callback: {e}", exc_info=True)
        try:
            query.edit_message_text("❌ Произошла ошибка при обработке запроса")
        except:
            pass
