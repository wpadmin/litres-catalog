from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.audiobook_service import AudiobookService
from app.templates import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="home")
async def home(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    service = AudiobookService(db)
    audiobooks, total_pages = await service.get_paginated(page=page, limit=24)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "audiobooks": audiobooks,
            "page": page,
            "total_pages": total_pages,
        }
    )
