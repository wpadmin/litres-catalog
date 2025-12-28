import os
import markdown
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.guide_service import GuideService
from app.templates import templates

router = APIRouter()

GUIDES_DIR = "guides"


@router.get("/guides/", response_class=HTMLResponse, name="guides_list")
async def guides_list(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Список всех подборок"""
    service = GuideService(db)
    guides = await service.get_all()

    return templates.TemplateResponse(
        "guides_list.html",
        {
            "request": request,
            "guides": guides,
        }
    )


@router.get("/guides/{slug}", response_class=HTMLResponse, name="guide_detail")
async def guide_detail(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Детальная страница подборки"""
    service = GuideService(db)
    guide = await service.get_by_slug(slug)

    if not guide:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )

    # Увеличиваем счётчик просмотров
    await service.increment_views(guide.id)

    # Читаем MD файл и конвертируем в HTML
    md_path = os.path.join(GUIDES_DIR, guide.md_file)
    content_html = ""

    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            content_html = markdown.markdown(
                md_content,
                extensions=['extra', 'codehilite', 'toc']
            )

    return templates.TemplateResponse(
        "guide_detail.html",
        {
            "request": request,
            "guide": guide,
            "content_html": content_html,
        }
    )
