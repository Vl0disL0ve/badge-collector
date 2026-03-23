import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models import Base

print("=" * 50)
print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ (SQLite)")
print("=" * 50)

try:
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✓ Таблицы созданы")
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Таблицы в базе данных ({len(tables)}):")
    for t in tables:
        print(f"   - {t}")
    
    print("\n✅ Инициализация завершена успешно!")
    print(f"Файл базы данных: badge_collector.db")
    
except Exception as e:
    print(f"✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()