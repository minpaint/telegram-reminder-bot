import logging
import time

from telegram.error import TelegramError

logger = logging.getLogger(__name__)


def monitor_bot_availability(bot, admin_id):
    """
    Проверяет доступность бота и уведомляет администратора о сбоях.
    """
    logger.info("Monitoring system initialized.")
    while True:
        try:
            bot.get_me()  # Тестовый запрос для проверки доступности бота
            time.sleep(60)  # Проверять каждые 60 секунд
        except TelegramError as e:
            logger.error(f"Bot is unavailable: {e}")
            notify_admin(bot, admin_id, f"🔴 Бот недоступен: {e}")
            time.sleep(300)  # Подождать 5 минут перед следующей попыткой
        except Exception as e:
            logger.exception(f"Unexpected error in monitoring: {e}")
            notify_admin(bot, admin_id, f"🔴 Критическая ошибка в мониторинге: {e}")
            time.sleep(300)  # Подождать 5 минут перед следующей попыткой


def notify_admin(bot, admin_id, message):
    """
    Отправляет уведомление админу.
    """
    try:
        bot.send_message(chat_id=admin_id, text=message)
    except TelegramError as e:
        logger.error(f"Failed to notify admin: {e}")
