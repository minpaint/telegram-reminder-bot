from sqlalchemy import inspect

from core.database import engine, Base


def check_tables():
    """Проверка существующих таблиц"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print("\nСуществующие таблицы:")
    for table in existing_tables:
        print(f"- {table}")


def init_database():
    """Инициализация базы данных и создание всех таблиц"""
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ База данных успешно инициализирована")
        # Проверяем созданные таблицы
        check_tables()
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")

if __name__ == "__main__":
    init_database()
