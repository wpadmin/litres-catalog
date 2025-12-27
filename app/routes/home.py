from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.audiobook_service import AudiobookService
from app.templates import templates
from app.cache import cache_get, cache_set
import json

router = APIRouter()

@router.get("/", response_class=HTMLResponse, name="home")
async def home(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    # Проверяем кеш
    cache_key = f"home_page_{page}"
    cached = await cache_get(cache_key)
    
    if cached:
        data = json.loads(cached)
        audiobooks = data["audiobooks"]
        total_pages = data["total_pages"]
    else:
        # Если кеша нет - запрос к БД
        service = AudiobookService(db)
        audiobooks, total_pages = await service.get_paginated(page=page, limit=24)
        
        # Сохраняем в кеш на 5 минут (ttl=300)
        cache_data = {
            "audiobooks": [
                {
                    "id": book.id,
                    "title": book.title,
                    "slug": book.slug,
                    "cover_url": book.cover_url,
                    "rating": book.rating,
                    "author_name": book.author_name,
                    "author_slug": book.author_slug,
                    "duration": book.duration,
                } for book in audiobooks
            ],
            "total_pages": total_pages
        }
        await cache_set(cache_key, json.dumps(cache_data), ttl=300)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "audiobooks": audiobooks,
            "page": page,
            "total_pages": total_pages,
        }
    )