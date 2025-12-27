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
                    "name": book.name,
                    "slug": book.slug,
                    "image_url": book.image_url,
                    "price": float(book.price) if book.price else 0,
                    "fragment_url": book.fragment_url,
                    "formats": book.formats,
                    "authors": [{"name": author.name, "slug": author.slug} for author in book.authors] if book.authors else [],
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