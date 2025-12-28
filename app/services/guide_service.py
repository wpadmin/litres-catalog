from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Guide


class GuideService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, limit: int = 100, offset: int = 0):
        """Получить список всех подборок"""
        query = (
            select(Guide)
            .order_by(Guide.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_slug(self, slug: str):
        """Получить подборку по slug с книгами"""
        query = (
            select(Guide)
            .where(Guide.slug == slug)
            .options(selectinload(Guide.audiobooks))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def increment_views(self, guide_id: int):
        """Увеличить счётчик просмотров"""
        guide = await self.db.get(Guide, guide_id)
        if guide:
            guide.views += 1
            await self.db.commit()
