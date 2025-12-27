from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.services.genre_service import GenreService
from app.models import Genre
from app.templates import templates

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
    offset = (page - 1) * limit

    result = await db.execute(
        select(Genre).where(Genre.parent_id == None).order_by(Genre.name).limit(limit).offset(offset)
    )
    genres = result.scalars().all()

    total = await db.scalar(select(func.count(Genre.id)).where(Genre.parent_id == None))
    total_pages = (total + limit - 1) // limit

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

    audiobooks, total_pages = await service.get_audiobooks_paginated(
        genre_id=genre.id,
        page=page,
        limit=24
    )

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
