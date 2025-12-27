import asyncio
import csv
import sys
import re
from pathlib import Path
from typing import List, Dict
from sqlalchemy.dialects.postgresql import insert

sys.path.append(str(Path(__file__).parent.parent))

from app.database import async_session_maker
from app.models import TextBook
from app.utils import normalize_title, extract_publisher_year


def parse_formats(params: str) -> str:
    """Парсинг форматов из поля params."""
    if not params:
        return ""

    formats_match = re.search(r'Форматы:([^|]+)', params)
    if formats_match:
        return formats_match.group(1).strip()

    return ""


async def bulk_upsert_textbooks(session, batch: List[dict]):
    """Массовый UPSERT текстовых книг."""
    if not batch:
        return

    try:
        stmt = insert(TextBook).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["litres_id"],
            set_={
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "price": stmt.excluded.price,
                "url": stmt.excluded.url,
                "image_url": stmt.excluded.image_url,
                "formats": stmt.excluded.formats,
                "publisher": stmt.excluded.publisher,
                "year": stmt.excluded.year,
                "normalized_key": stmt.excluded.normalized_key,
                "author_normalized": stmt.excluded.author_normalized,
            }
        )
        await session.execute(stmt)
    except Exception as e:
        print(f"\n[ERROR] Batch insert failed: {str(e)[:500]}")
        print(f"Trying row-by-row insert for {len(batch)} items...")

        for item in batch:
            try:
                stmt = insert(TextBook).values([item])
                stmt = stmt.on_conflict_do_update(
                    index_elements=["litres_id"],
                    set_={
                        "name": stmt.excluded.name,
                        "description": stmt.excluded.description,
                        "price": stmt.excluded.price,
                        "url": stmt.excluded.url,
                        "image_url": stmt.excluded.image_url,
                        "formats": stmt.excluded.formats,
                        "publisher": stmt.excluded.publisher,
                        "year": stmt.excluded.year,
                        "normalized_key": stmt.excluded.normalized_key,
                        "author_normalized": stmt.excluded.author_normalized,
                    }
                )
                await session.execute(stmt)
            except Exception as row_error:
                print(f"Failed item litres_id={item.get('litres_id')}: {str(row_error)[:200]}")
                continue


async def import_textbooks(csv_file_path: str, batch_size: int = 5000):
    # Отключаем SQLAlchemy логи для чистоты вывода
    import logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # Подсчёт строк
    with open(csv_file_path, "r", encoding="utf-8-sig") as file:
        total_rows = sum(1 for _ in file) - 1

    async with async_session_maker() as session:
        # Оптимизация для массового импорта
        from sqlalchemy import text
        await session.execute(text("SET session_replication_role = replica;"))

        batch = []
        stats = {"processed": 0, "errors": 0, "skipped": 0}

        print(f"Импорт {total_rows:,} строк...")

        with open(csv_file_path, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file, delimiter=";")

            processed_count = 0
            for row in reader:
                processed_count += 1
                if processed_count % 50000 == 0:
                    print(f"{processed_count:,} / {total_rows:,}")
                try:
                    # Проверяем, что это не аудиокнига
                    url = row.get("url", "")
                    if "/audiobook/" in url:
                        stats["skipped"] += 1
                        continue

                    litres_id = int(row["id"])
                    name = row["name"]
                    description = row.get("description", "")
                    author = row.get("brand", "").strip()
                    price_str = row.get("price", "0")
                    image_url = row.get("image", "")
                    params = row.get("params", "")

                    # Парсим форматы
                    formats = parse_formats(params)

                    # Извлекаем издательство и год
                    publisher, year = extract_publisher_year(description)

                    # Нормализация для связывания
                    normalized_key = normalize_title(name)
                    author_normalized = author.lower()

                    # Валидация цены
                    try:
                        price = float(price_str) if price_str else None
                    except ValueError:
                        price = None

                    batch.append({
                        "litres_id": litres_id,
                        "name": name[:500] if name else "",
                        "description": description[:50000] if description else None,
                        "price": price,
                        "url": url[:1000] if url else "",
                        "image_url": image_url[:1000] if image_url else None,
                        "formats": formats[:500] if formats else None,
                        "publisher": publisher[:255] if publisher else None,
                        "year": year,
                        "normalized_key": normalized_key[:500] if normalized_key else "",
                        "author_normalized": author_normalized[:255] if author_normalized else "",
                    })

                    if len(batch) >= batch_size:
                        await bulk_upsert_textbooks(session, batch)
                        await session.commit()
                        stats["processed"] += len(batch)
                        batch = []

                except Exception as e:
                    stats["errors"] += 1
                    if stats["errors"] < 10:
                        print(f"Error on row {processed_count}: {str(e)[:200]}")
                    continue

            if batch:
                await bulk_upsert_textbooks(session, batch)
                await session.commit()
                stats["processed"] += len(batch)

        # Возвращаем триггеры и индексы
        await session.execute(text("SET session_replication_role = DEFAULT;"))
        await session.commit()

        print(f"\nDone: {stats['processed']:,} | Skipped: {stats['skipped']:,} | Errors: {stats['errors']:,}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Импорт текстовых книг из CSV")
    parser.add_argument("--file", type=str, default="litresru-full.csv", help="Путь к CSV файлу")
    parser.add_argument("--batch-size", type=int, default=5000, help="Размер батча")
    args = parser.parse_args()

    asyncio.run(import_textbooks(args.file, batch_size=args.batch_size))
