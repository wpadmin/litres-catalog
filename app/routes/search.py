from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.search_service import SearchService
from app.templates import templates

router = APIRouter()


@router.get("/search", response_class=HTMLResponse, name="search")
async def search(
    request: Request,
    q: str = "",
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    if not q:
        return templates.TemplateResponse(
            "search.html",
            {"request": request, "audiobooks": [], "query": q}
        )

    service = SearchService(db)
    audiobooks, total_pages = await service.search_audiobooks(
        query=q,
        page=page,
        limit=24
    )

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "audiobooks": audiobooks,
            "query": q,
            "page": page,
            "total_pages": total_pages,
        }
    )


@router.get("/api/search", response_class=JSONResponse)
async def api_search(
    q: str = "",
    db: AsyncSession = Depends(get_db)
):
    if not q or len(q) < 2:
        return {"results": []}

    service = SearchService(db)
    results = await service.search_autocomplete(query=q, limit=10)

    return {"results": results}
