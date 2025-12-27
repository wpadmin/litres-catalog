from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.services.genre_service import GenreService
from app.models import Genre
from app.templates import templates
from app.cache import cache_get, cache_set
import json

router = APIRouter()


@router.get("/api/genres", response_class=JSONResponse, name="genres_list_api")
async def genres_list_api(
    request: Request,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit

    result = await db.execute(
        select(Genre).where(Genre.parent_id == None).order_by(Genre.name).limit(limit).offset(offset)
    )
    genres = result.scalars().all()

    total = await db.scalar(select(func.count(Genre.id)).where(Genre.parent_id == None))

    return {
        "genres": [{"name": g.name, "slug": g.slug} for g in genres],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/genres", response_class=HTMLResponse, name="genres_list")
async def genres_list(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    limit = 100
    cache_key = f"genres_list_{page}"
    cached = await cache_get(cache_key)

    if cached:
        data = json.loads(cached)
        genres = data["genres"]
        total = data["total"]
        total_pages = data["total_pages"]
    else:
        offset = (page - 1) * limit

        result = await db.execute(
            select(Genre).where(Genre.parent_id == None).order_by(Genre.name).limit(limit).offset(offset)
        )
        genres_objs = result.scalars().all()

        total = await db.scalar(select(func.count(Genre.id)).where(Genre.parent_id == None))
        total_pages = (total + limit - 1) // limit

        cache_data = {
            "genres": [{"id": g.id, "name": g.name, "slug": g.slug} for g in genres_objs],
            "total": total,
            "total_pages": total_pages
        }
        await cache_set(cache_key, json.dumps(cache_data), ttl=600)
        genres = cache_data["genres"]

    return templates.TemplateResponse(
        "genres_list.html",
        {
            "request": request,
            "genres": genres,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        }
    )


@router.get("/genre/{slug}", response_class=HTMLResponse, name="genre_detail")
async def genre_detail(
    slug: str,
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    service = GenreService(db)
    genre = await service.get_by_slug(slug)

    if not genre:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )

    cache_key = f"genre_{slug}_books_{page}"
    cached = await cache_get(cache_key)

    if cached:
        data = json.loads(cached)
        audiobooks = data["audiobooks"]
        total_pages = data["total_pages"]
    else:
        audiobooks_objs, total_pages = await service.get_audiobooks_paginated(
            genre_id=genre.id,
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
        "genre_detail.html",
        {
            "request": request,
            "genre": genre,
            "audiobooks": audiobooks,
            "page": page,
            "total_pages": total_pages,
        }
    )
