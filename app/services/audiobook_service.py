from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Audiobook


class AudiobookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_slug(self, slug: str) -> Audiobook | None:
        query = (
            select(Audiobook)
            .options(
                selectinload(Audiobook.authors),
                selectinload(Audiobook.genres),
                selectinload(Audiobook.text_versions)
            )
            .where(Audiobook.slug == slug)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        page: int = 1,
        limit: int = 24
    ) -> tuple[list[Audiobook], int]:
        offset = (page - 1) * limit

        query = (
            select(Audiobook)
            .options(selectinload(Audiobook.authors), selectinload(Audiobook.genres))
            .order_by(Audiobook.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        audiobooks = result.scalars().all()

        count_query = select(func.count(Audiobook.id))
        total_count = await self.db.scalar(count_query)
        total_pages = (total_count + limit - 1) // limit

        return list(audiobooks), total_pages
