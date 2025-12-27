from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Audiobook


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_audiobooks(
        self,
        query: str,
        page: int = 1,
        limit: int = 24
    ) -> tuple[list[Audiobook], int]:
        offset = (page - 1) * limit

        search_query = (
            select(Audiobook)
            .where(Audiobook.name.ilike(f"%{query}%"))
            .options(selectinload(Audiobook.authors), selectinload(Audiobook.genres))
            .order_by(Audiobook.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(search_query)
        audiobooks = result.scalars().all()

        count_query = select(func.count(Audiobook.id)).where(
            Audiobook.name.ilike(f"%{query}%")
        )
        total_count = await self.db.scalar(count_query)
        total_pages = (total_count + limit - 1) // limit

        return list(audiobooks), total_pages

    async def search_autocomplete(self, query: str, limit: int = 10) -> list[dict]:
        search_query = (
            select(Audiobook)
            .where(Audiobook.name.ilike(f"%{query}%"))
            .options(selectinload(Audiobook.authors))
            .order_by(Audiobook.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(search_query)
        audiobooks = result.scalars().all()

        return [
            {
                "id": book.id,
                "slug": book.slug,
                "name": book.name,
                "authors": ", ".join([a.name for a in book.authors]) if book.authors else "",
                "price": float(book.price),
                "image_url": book.image_url or "",
            }
            for book in audiobooks
        ]
