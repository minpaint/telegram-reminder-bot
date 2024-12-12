from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, BigInteger

from core.database import Base


class Event(Base):
    __tablename__ = "events"
    event_id = Column(Integer, primary_key=True)
    creator_id = Column(BigInteger)  # это telegram_id создателя
    file_name = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    event_time = Column(Time, nullable=False)
    next_reminder = Column(DateTime, nullable=False)
    periodicity = Column(Integer, nullable=True)
    repeat_type = Column(String, nullable=True)
    remind_before = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    responsible_telegram_ids = Column(BigInteger, nullable=True)  # Поле для ID ответственного
    responsible_email = Column(String, nullable=True)