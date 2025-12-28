from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.services.author_service import AuthorService
from app.models import Author
from app.templates import templates
from app.cache import cache_get, cache_set
import json

router = APIRouter()


def get_last_name(full_name: str) -> str:
    """Извлекает фамилию (последнее слово) из полного имени."""
    return full_name.strip().split()[-1] if full_name else ""


@router.get("/api/authors", response_class=JSONResponse, name="authors_list_api")
async def authors_list_api(
    request: Request,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit

    result = await db.execute(
        select(Author).order_by(Author.name).limit(limit).offset(offset)
    )
    authors = result.scalars().all()

    total = await db.scalar(select(func.count(Author.id)))

    return {
        "authors": [{"name": a.name, "slug": a.slug} for a in authors],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/authors", response_class=HTMLResponse, name="authors_list")
async def authors_list(
    request: Request,
    page: int = 1,
    letter: str = None,
    db: AsyncSession = Depends(get_db)
):
    limit = 100
    cache_key = f"authors_list_{page}_{letter or 'all'}"
    cached = await cache_get(cache_key)

    if cached:
        data = json.loads(cached)
        authors = data["authors"]
        total = data["total"]
        total_pages = data["total_pages"]
    else:
        offset = (page - 1) * limit

        # Получаем всех авторов
        query = select(Author)
        result = await db.execute(query)
        all_authors = result.scalars().all()

        # Фильтруем и сортируем в Python по фамилии
        if letter:
            filtered_authors = [
                a for a in all_authors
                if get_last_name(a.name).upper().startswith(letter.upper())
            ]
        else:
            filtered_authors = all_authors

        # Сортируем по фамилии
        sorted_authors = sorted(
            filtered_authors,
            key=lambda a: get_last_name(a.name).lower()
        )

        total = len(sorted_authors)
        total_pages = (total + limit - 1) // limit

        # Применяем пагинацию
        start = offset
        end = offset + limit
        paginated_authors = sorted_authors[start:end]

        cache_data = {
            "authors": [{"id": a.id, "name": a.name, "slug": a.slug} for a in paginated_authors],
            "total": total,
            "total_pages": total_pages
        }
        await cache_set(cache_key, json.dumps(cache_data), ttl=600)
        authors = cache_data["authors"]

    return templates.TemplateResponse(
        "authors_list.html",
        {
            "request": request,
            "authors": authors,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        }
    )


@router.get("/api/author/{slug}/books", response_class=JSONResponse)
async def author_books_api(
    slug: str,
    offset: int = 0,
    limit: int = 6,
    db: AsyncSession = Depends(get_db)
):
    """API карусели для книг автора"""
    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload
    from app.models import Audiobook

    service = AuthorService(db)
    author = await service.get_by_slug(slug)

    if not author:
        return {"books": [], "has_more": False, "total": 0}

    # Получаем общее количество книг
    count_query = (
        select(func.count(Audiobook.id))
        .join(Audiobook.authors)
        .where(Author.id == author.id)
    )
    total = await db.scalar(count_query)

    # Получаем книги с пагинацией
    query = (
        select(Audiobook)
        .join(Audiobook.authors)
        .where(Author.id == author.id)
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
                "slug": b.slug,
                "name": b.name,
                "image_url": b.image_url,
                "price": float(b.price),
                "genres": [g.name for g in b.genres] if b.genres else [],
                "fragment_url": b.fragment_url,
                "authors": [a.name for a in b.authors],
            }
            for b in books
        ],
        "has_more": (offset + limit) < total,
        "total": total
    }


@router.get("/author/{slug}", response_class=HTMLResponse, name="author_detail")
async def author_detail(
    slug: str,
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    service = AuthorService(db)
    author = await service.get_by_slug(slug)

    if not author:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )

    cache_key = f"author_{slug}_books_{page}"
    cached = await cache_get(cache_key)

    if cached:
        data = json.loads(cached)
        audiobooks = data["audiobooks"]
        total_pages = data["total_pages"]
    else:
        audiobooks_objs, total_pages = await service.get_audiobooks_paginated(
            author_id=author.id,
            page=page,
            limit=24
        )

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
                    "authors": [{"name": a.name, "slug": a.slug} for a in book.authors] if book.authors else [],
                } for book in audiobooks_objs
            ],
            "total_pages": total_pages
        }
        await cache_set(cache_key, json.dumps(cache_data), ttl=600)
        audiobooks = cache_data["audiobooks"]

    return templates.TemplateResponse(
        "author_detail.html",
        {
            "request": request,
            "author": author,
            "audiobooks": audiobooks,
            "page": page,
            "total_pages": total_pages,
        }
    )
