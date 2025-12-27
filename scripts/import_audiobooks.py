import asyncio
import csv
import sys
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from tqdm import tqdm
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

sys.path.append(str(Path(__file__).parent.parent))

from app.database import async_session_maker, engine
from app.models import Audiobook, Author, Genre, audiobook_author, audiobook_genre
from app.utils import slugify


def parse_formats_and_fragment(params: str) -> tuple[dict, str | None]:
    if not params:
        return {}, None

    parts = params.split("|")
    formats = {}
    fragment_url = None

    for part in parts:
        if part.startswith("Форматы:"):
            format_list = part.replace("Форматы:", "").strip().split(",")
            formats = {"formats": format_list}
        elif part.startswith("Фрагмент:"):
            fragment_url = part.replace("Фрагмент:", "").strip()

    return formats, fragment_url


async def optimize_for_bulk_load(session):
    """Оптимизация БД для массовой загрузки."""
    await session.execute(text("SET session_replication_role = replica"))
    await session.execute(text("SET maintenance_work_mem = '512MB'"))
    await session.commit()


async def restore_after_bulk_load(session):
    """Восстановление настроек после загрузки."""
    await session.execute(text("SET session_replication_role = DEFAULT"))
    await session.execute(text("ANALYZE authors"))
    await session.execute(text("ANALYZE genres"))
    await session.execute(text("ANALYZE audiobooks"))
    await session.commit()


async def bulk_insert_authors(session, author_names: set) -> Dict[str, int]:
    """Массовая вставка авторов одним запросом."""
    result = await session.execute(select(Author.id, Author.name))
    existing = {name: author_id for author_id, name in result.fetchall()}

    new_authors = []
    result = await session.execute(select(Author.slug))
    existing_slugs = {slug for (slug,) in result.fetchall()}
    slug_set = set(existing_slugs)

    for name in author_names:
        # Обрезаем слишком длинные имена авторов
        if len(name) > 255:
            name = name[:252] + "..."

        if name not in existing:
            base_slug = slugify(name)
            # Обрезаем slug до 240 символов
            if len(base_slug) > 240:
                base_slug = base_slug[:240]

            slug = base_slug
            counter = 1

            while slug in slug_set:
                slug = f"{base_slug}-{counter}"
                if len(slug) > 255:
                    base_slug = base_slug[:230]
                    slug = f"{base_slug}-{counter}"
                counter += 1

            slug_set.add(slug)
            new_authors.append({"name": name, "slug": slug})

    if new_authors:
        # Вставляем батчами по 5000 (PostgreSQL limit 32767 params / 2 fields = ~16000)
        batch_size = 5000
        for i in range(0, len(new_authors), batch_size):
            batch = new_authors[i:i + batch_size]
            stmt = insert(Author).values(batch).returning(Author.id, Author.name)
            result = await session.execute(stmt)
            for author_id, name in result.fetchall():
                existing[name] = author_id
            await session.commit()

    return existing


async def bulk_insert_genres(session, categories: set) -> Dict[str, list]:
    """Массовая вставка жанров."""
    result = await session.execute(select(Genre.id, Genre.name, Genre.parent_id))
    existing_genres = {}
    for genre_id, name, parent_id in result.fetchall():
        key = (name, parent_id)
        existing_genres[key] = genre_id

    result = await session.execute(select(Genre.slug))
    existing_slugs = {slug for (slug,) in result.fetchall()}
    slug_set = set(existing_slugs)

    genre_cache = {}
    new_genres = []

    for category in sorted(categories):
        genre_names = [g.strip() for g in category.split(">") if g.strip()]
        genre_ids = []
        parent_id = None

        for genre_name in genre_names:
            # Обрезаем слишком длинные названия
            if len(genre_name) > 255:
                genre_name = genre_name[:252] + "..."

            key = (genre_name, parent_id)

            if key in existing_genres:
                genre_id = existing_genres[key]
            else:
                base_slug = slugify(genre_name)
                # Обрезаем slug до 240 символов (оставляем место для счетчика)
                if len(base_slug) > 240:
                    base_slug = base_slug[:240]

                slug = base_slug
                counter = 1

                while slug in slug_set:
                    slug = f"{base_slug}-{counter}"
                    if len(slug) > 255:
                        # Если даже с счетчиком выходит за лимит, обрезаем base_slug еще короче
                        base_slug = base_slug[:230]
                        slug = f"{base_slug}-{counter}"
                    counter += 1

                slug_set.add(slug)
                new_genres.append({"name": genre_name, "slug": slug, "parent_id": parent_id})

                genre = Genre(name=genre_name, slug=slug, parent_id=parent_id)
                session.add(genre)
                await session.flush()

                genre_id = genre.id
                existing_genres[key] = genre_id

            genre_ids.append(genre_id)
            parent_id = genre_id

        if genre_ids:  # Добавляем только если есть валидные жанры
            genre_cache[category] = genre_ids

    await session.commit()
    return genre_cache


async def bulk_upsert_audiobooks(session, batch: List[dict]) -> Dict[int, int]:
    """Массовый UPSERT аудиокниг через INSERT ... ON CONFLICT."""
    if not batch:
        return {}

    stmt = insert(Audiobook).values(batch)
    stmt = stmt.on_conflict_do_update(
        index_elements=["litres_id"],
        set_={
            "name": stmt.excluded.name,
            "slug": stmt.excluded.slug,
            "description": stmt.excluded.description,
            "price": stmt.excluded.price,
            "url": stmt.excluded.url,
            "image_url": stmt.excluded.image_url,
            "formats": stmt.excluded.formats,
            "fragment_url": stmt.excluded.fragment_url,
        }
    )
    await session.execute(stmt)
    await session.commit()

    litres_ids = [b["litres_id"] for b in batch]
    result = await session.execute(
        select(Audiobook.id, Audiobook.litres_id).where(Audiobook.litres_id.in_(litres_ids))
    )
    return {litres_id: ab_id for ab_id, litres_id in result.fetchall()}


async def bulk_insert_relations(session, audiobook_ids: Dict[int, int], author_rels: List[dict], genre_rels: dict):
    """Массовая вставка связей M2M."""
    audiobook_id_list = list(audiobook_ids.values())

    if audiobook_id_list:
        await session.execute(
            audiobook_author.delete().where(
                audiobook_author.c.audiobook_id.in_(audiobook_id_list)
            )
        )
        await session.execute(
            audiobook_genre.delete().where(
                audiobook_genre.c.audiobook_id.in_(audiobook_id_list)
            )
        )

    if author_rels:
        author_links = []
        for rel in author_rels:
            audiobook_id = audiobook_ids.get(rel["litres_id"])
            if audiobook_id:
                author_links.append({
                    "audiobook_id": audiobook_id,
                    "author_id": rel["author_id"]
                })

        if author_links:
            await session.execute(insert(audiobook_author).values(author_links))

    if genre_rels:
        genre_links = []
        for litres_id, genre_ids in genre_rels.items():
            audiobook_id = audiobook_ids.get(litres_id)
            if audiobook_id:
                for genre_id in genre_ids:
                    genre_links.append({
                        "audiobook_id": audiobook_id,
                        "genre_id": genre_id
                    })

        if genre_links:
            await session.execute(insert(audiobook_genre).values(genre_links))

    await session.commit()


async def import_csv_data(csv_file_path: str, batch_size: int = 1000):
    # Отключаем SQLAlchemy логи для чистоты вывода
    import logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    print(f"\nИмпорт из {csv_file_path}...")
    print("Чтение CSV в память...")

    with open(csv_file_path, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file, delimiter=";")
        rows = list(reader)
        total_rows = len(rows)

    print(f"Загружено {total_rows:,} записей в память\n")

    print("Анализ уникальных данных...")
    author_names = set()
    categories = set()

    for row in tqdm(rows, desc="Анализ", unit=" строк"):
        brand = row.get("brand", "Неизвестный автор").strip()
        category = row.get("category", "").strip()

        author_names.add(brand)
        if category:
            categories.add(category)

    print(f"\nУникальных авторов: {len(author_names):,}")
    print(f"Уникальных категорий: {len(categories):,}\n")

    async with async_session_maker() as session:
        print("Оптимизация БД для массовой загрузки...")
        await optimize_for_bulk_load(session)

        print("Массовая вставка авторов...")
        author_map = await bulk_insert_authors(session, author_names)
        print(f"Создано/найдено {len(author_map):,} авторов")

        print("Массовая вставка жанров...")
        genre_cache = await bulk_insert_genres(session, categories)
        print(f"Создано/найдено {len(genre_cache):,} жанровых путей\n")

    print(f"Импорт аудиокниг батчами по {batch_size}...\n")

    async with async_session_maker() as session:
        batch = []
        author_relations = []
        genre_relations = defaultdict(list)
        stats = {"processed": 0, "errors": 0}

        pbar = tqdm(rows, desc="Импорт", unit=" книг")

        for row in pbar:
            try:
                litres_id = int(row["id"])
                name = row["name"]
                description = row.get("description", "")
                category = row.get("category", "").strip()
                price = float(row.get("price", 0))
                url = row["url"]
                image_url = row.get("image", "")
                brand = row.get("brand", "Неизвестный автор").strip()
                params = row.get("params", "")

                formats, fragment_url = parse_formats_and_fragment(params)
                author_id = author_map.get(brand)

                if not author_id:
                    stats["errors"] += 1
                    continue

                batch.append({
                    "litres_id": litres_id,
                    "name": name,
                    "slug": slugify(f"{name}-{litres_id}"),
                    "description": description,
                    "price": price,
                    "url": url,
                    "image_url": image_url,
                    "formats": formats,
                    "fragment_url": fragment_url,
                })

                author_relations.append({"litres_id": litres_id, "author_id": author_id})

                if category and category in genre_cache:
                    genre_relations[litres_id] = genre_cache[category]

                if len(batch) >= batch_size:
                    audiobook_ids = await bulk_upsert_audiobooks(session, batch)
                    await bulk_insert_relations(session, audiobook_ids, author_relations, genre_relations)

                    stats["processed"] += len(batch)
                    pbar.set_postfix({"обработано": f"{stats['processed']:,}", "ошибок": stats["errors"]})

                    batch = []
                    author_relations = []
                    genre_relations = defaultdict(list)

            except Exception as e:
                stats["errors"] += 1
                continue

        if batch:
            audiobook_ids = await bulk_upsert_audiobooks(session, batch)
            await bulk_insert_relations(session, audiobook_ids, author_relations, genre_relations)
            stats["processed"] += len(batch)

        print("\nВосстановление настроек и ANALYZE...")
        await restore_after_bulk_load(session)

    print(f"\nИмпорт завершён!")
    print(f"Обработано: {stats['processed']:,} | Ошибок: {stats['errors']:,}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Импорт аудиокниг из CSV")
    parser.add_argument("--file", type=str, default="litresru.csv", help="Путь к CSV файлу")
    parser.add_argument("--batch-size", type=int, default=1000, help="Размер батча (по умолчанию 1000)")
    args = parser.parse_args()

    asyncio.run(import_csv_data(args.file, batch_size=args.batch_size))
