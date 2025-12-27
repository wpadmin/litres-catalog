from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.audiobook_service import AudiobookService
from app.templates import templates

router = APIRouter()


@router.get("/audiobook/{slug}", response_class=HTMLResponse, name="audiobook_detail")
async def audiobook_detail(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    service = AudiobookService(db)
    audiobook = await service.get_by_slug(slug)

    if not audiobook:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )

    return templates.TemplateResponse(
        "audiobook_detail.html",
        {
            "request": request,
            "audiobook": audiobook,
        }
    )
