"""
Одноразовый скрипт для пометки топовых книг из litresru-top.csv
Запускать на проде ОДИН РАЗ после применения миграции
"""
import csv
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from app.database import async_session_maker
from app.models import Audiobook


async def mark_top_books():
    csv_path = Path(__file__).parent.parent / "litresru-top.csv"

    if not csv_path.exists():
        print(f"ОШИБКА: Файл {csv_path} не найден!")
        return

    # Читаем CSV с топ-500
    litres_ids = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            litres_ids.append(int(row['id']))

    print(f"Загружено {len(litres_ids)} книг из топ-500")

    async with async_session_maker() as session:
        # Помечаем топовые книги
        stmt = (
            update(Audiobook)
            .where(Audiobook.litres_id.in_(litres_ids))
            .values(is_top=True)
        )
        result = await session.execute(stmt)
        await session.commit()

        print(f"✓ Помечено {result.rowcount} топовых аудиокниг")

        # Проверка
        query = select(Audiobook).where(Audiobook.is_top == True)
        result = await session.execute(query)
        top_books = result.scalars().all()

        print(f"✓ Всего топовых книг в базе: {len(top_books)}")


if __name__ == "__main__":
    print("Запуск пометки топовых книг...")
    asyncio.run(mark_top_books())
    print("Готово!")
