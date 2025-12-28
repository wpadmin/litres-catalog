from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Guide
from redis.asyncio import Redis


class GuideService:
    def __init__(self, db: AsyncSession, redis: Redis = None):
        self.db = db
        self.redis = redis

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
        """Получить подборку по slug"""
        query = select(Guide).where(Guide.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def increment_views(self, guide_id: int, client_ip: str):
        """Увеличить счётчик просмотров (ограничение по IP)"""
        if self.redis:
            cache_key = f"guide_view:{guide_id}:{client_ip}"
            exists = await self.redis.exists(cache_key)
            if exists:
                return
            await self.redis.setex(cache_key, 3600, "1")

        guide = await self.db.get(Guide, guide_id)
        if guide:
            guide.views += 1
            await self.db.commit()
