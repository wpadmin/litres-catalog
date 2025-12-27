from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.services.audiobook_service import AudiobookService
from app.models import Audiobook
from app.templates import templates
from app.cache import cache_get, cache_set
import json

router = APIRouter()

@router.get("/", response_class=HTMLResponse, name="home")
async def home(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Проверяем кеш для первых 24 топовых книг
    cache_key = "home_top_books_initial"
    cached = await cache_get(cache_key)

    if cached:
        data = json.loads(cached)
        audiobooks = data["audiobooks"]
        total = data["total"]
    else:
        # Загружаем первые 24 топовые книги
        limit = 24
        count_query = select(func.count(Audiobook.id)).where(Audiobook.is_top == True)
        total = await db.scalar(count_query)

        query = (
            select(Audiobook)
            .where(Audiobook.is_top == True)
            .options(selectinload(Audiobook.authors), selectinload(Audiobook.genres))
            .order_by(Audiobook.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        books = list(result.scalars().all())

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
                } for book in books
            ],
            "total": total
        }
        await cache_set(cache_key, json.dumps(cache_data), ttl=300)
        audiobooks = cache_data["audiobooks"]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "audiobooks": audiobooks,
            "total": total,
        }
    )


@router.get("/api/top-books", response_class=JSONResponse, name="top_books_api")
async def top_books_api(
    offset: int = 0,
    limit: int = 24,
    db: AsyncSession = Depends(get_db)
):
    # Получаем общее количество топовых книг
    count_query = select(func.count(Audiobook.id)).where(Audiobook.is_top == True)
    total = await db.scalar(count_query)

    # Получаем книги с пагинацией
    query = (
        select(Audiobook)
        .where(Audiobook.is_top == True)
        .options(selectinload(Audiobook.authors), selectinload(Audiobook.genres))
        .order_by(Audiobook.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    books = list(result.scalars().all())

    return {
        "books": [
            {
                "id": b.id,
                "slug": b.slug,
                "name": b.name,
                "image_url": b.image_url,
                "price": float(b.price) if b.price else 0,
                "fragment_url": b.fragment_url,
                "formats": b.formats,
                "authors": [{"name": a.name, "slug": a.slug} for a in b.authors] if b.authors else [],
            }
            for b in books
        ],
        "has_more": (offset + limit) < total,
        "total": total
    }