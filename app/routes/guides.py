import os
import markdown
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, get_redis
from app.services.guide_service import GuideService
from app.templates import templates
from redis.asyncio import Redis

router = APIRouter()

GUIDES_DIR = "articles"


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
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Детальная страница подборки"""
    service = GuideService(db, redis)
    guide = await service.get_by_slug(slug)

    if not guide:
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )

    # Получаем IP клиента
    client_ip = request.client.host if request.client else "unknown"

    # Увеличиваем счётчик просмотров (с ограничением по IP)
    await service.increment_views(guide.id, client_ip)

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
            # Add target="_blank" to all external links
            import re
            content_html = re.sub(
                r'<a href="(https?://[^"]+)"',
                r'<a href="\1" target="_blank" rel="noopener noreferrer"',
                content_html
            )

    return templates.TemplateResponse(
        "guide_detail.html",
        {
            "request": request,
            "guide": guide,
            "content_html": content_html,
        }
    )
