"""Финальный скрипт связывания через готовые normalized поля."""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text, select, func

sys.path.append(str(Path(__file__).parent.parent))

from app.database import async_session_maker
from app.models import Audiobook, TextBook, audiobook_textbook


async def link_versions():
    """Связывание через готовые normalized поля."""
    import logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    print("\n" + "="*60)
    print("Svyazyvanie audioknig s tekstovymi izdaniyami")
    print("="*60 + "\n")

    async with async_session_maker() as session:
        # Статистика перед
        total_audio = await session.scalar(select(func.count(Audiobook.id)))
        total_text = await session.scalar(select(func.count(TextBook.id)))
        existing_links = await session.scalar(select(func.count()).select_from(audiobook_textbook))

        print(f"[*] Audioknig: {total_audio:,}")
        print(f"[*] Tekstovyh knig: {total_text:,}")
        print(f"[*] Sushestv. svyazej: {existing_links:,}\n")

        # Связывание через прямое совпадение normalized полей
        print("[*] Vypolnyaetsya svyazyvanie...\n")

        result = await session.execute(text("""
            WITH matches AS (
                SELECT DISTINCT
                    a.id as audiobook_id,
                    t.id as textbook_id
                FROM audiobooks a
                JOIN text_books t ON
                    t.normalized_key = a.normalized_key
                    AND t.author_normalized = a.author_normalized
                WHERE a.normalized_key IS NOT NULL
                    AND a.normalized_key != ''
                    AND NOT EXISTS (
                        SELECT 1 FROM audiobook_textbook at
                        WHERE at.audiobook_id = a.id
                        AND at.textbook_id = t.id
                    )
            )
            INSERT INTO audiobook_textbook (audiobook_id, textbook_id, created_at)
            SELECT audiobook_id, textbook_id, NOW()
            FROM matches
            ON CONFLICT DO NOTHING
            RETURNING audiobook_id
        """))

        new_links = len(result.fetchall())
        await session.commit()

        print(f"[OK] Sozdano novyh svyazej: {new_links:,}\n")

        # Финальная статистика
        total_links = await session.scalar(select(func.count()).select_from(audiobook_textbook))
        audio_with_text = await session.scalar(
            select(func.count(func.distinct(audiobook_textbook.c.audiobook_id)))
            .select_from(audiobook_textbook)
        )

        # Среднее количество версий
        subq = (
            select(
                audiobook_textbook.c.audiobook_id,
                func.count(audiobook_textbook.c.textbook_id).label('versions_count')
            )
            .select_from(audiobook_textbook)
            .group_by(audiobook_textbook.c.audiobook_id)
            .subquery()
        )
        avg_versions = await session.scalar(select(func.avg(subq.c.versions_count)))

        coverage = (audio_with_text / total_audio * 100) if total_audio > 0 else 0

        print("="*60)
        print("FINALNAYA STATISTIKA:")
        print("="*60)
        print(f"Vsego svyazej:            {total_links:,}")
        print(f"Audioknig s tekstom:      {audio_with_text:,} ({coverage:.1f}%)")
        if avg_versions:
            print(f"Srednee versij na knigu:  {avg_versions:.2f}")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(link_versions())
