import pytz
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config.settings import DATABASE_URL


class SchedulerManager:
    """Менеджер планировщика задач"""

    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(url=DATABASE_URL)
        }
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone=pytz.timezone('Europe/Moscow')
        )

    def start(self):
        """Запуск планировщика"""
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()

    def add_notification_job(self, job_id, func, run_date, replace_existing=True, **kwargs):
        """Добавление задачи отправки уведомления"""
        self.scheduler.add_job(
            func,
            'date',
            run_date=run_date,
            id=str(job_id),
            replace_existing=replace_existing,
            kwargs=kwargs
        )

    def remove_job(self, job_id):
        """Удаление задачи"""
        try:
            self.scheduler.remove_job(str(job_id))
            return True
        except:
            return False
