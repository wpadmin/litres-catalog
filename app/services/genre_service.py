from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Genre, Audiobook


class GenreService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_slug(self, slug: str) -> Genre | None:
        query = select(Genre).where(Genre.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_audiobooks_paginated(
        self,
        genre_id: int,
        page: int = 1,
        limit: int = 24
    ) -> tuple[list[Audiobook], int]:
        offset = (page - 1) * limit

        audiobooks_query = (
            select(Audiobook)
            .join(Audiobook.genres)
            .where(Genre.id == genre_id)
            .options(selectinload(Audiobook.authors), selectinload(Audiobook.genres))
            .order_by(Audiobook.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(audiobooks_query)
        audiobooks = result.scalars().all()

        count_query = (
            select(func.count(Audiobook.id))
            .join(Audiobook.genres)
            .where(Genre.id == genre_id)
        )
        total_count = await self.db.scalar(count_query)
        total_pages = (total_count + limit - 1) // limit

        return list(audiobooks), total_pages
