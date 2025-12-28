from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Audiobook, Author, Genre, Guide
from app.cache import cache_get, cache_set
import os

router = APIRouter()

CACHE_TTL = 604800  # 7 дней
CHUNK_SIZE = 30000  # Разбивка по 30к записей


def generate_url_entry(loc: str, lastmod: str = None, changefreq: str = "weekly", priority: str = "0.8") -> str:
    """Генерирует XML для одного URL"""
    lastmod_str = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    return f"""  <url>
    <loc>{loc}</loc>{lastmod_str}
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""


def wrap_urlset(urls: str) -> str:
    """Оборачивает URLs в XML urlset"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""


@router.get("/sitemap.xml")
async def sitemap_index(db: AsyncSession = Depends(get_db)):
    """Главный sitemap index"""
    cache_key = "sitemap_index"
    cached = await cache_get(cache_key)

    if cached:
        return Response(content=cached, media_type="application/xml")

    # Считаем количество аудиокниг для разбивки
    result = await db.execute(select(func.count(Audiobook.id)))
    total_audiobooks = result.scalar()

    # Количество файлов для аудиокниг
    audiobook_chunks = (total_audiobooks + CHUNK_SIZE - 1) // CHUNK_SIZE

    # Генерируем sitemap index
    sitemaps = [
        f"""  <sitemap>
    <loc>https://bigear.ru/sitemap_static.xml</loc>
  </sitemap>"""
    ]

    # Добавляем все чанки аудиокниг
    for i in range(1, audiobook_chunks + 1):
        sitemaps.append(f"""  <sitemap>
    <loc>https://bigear.ru/sitemap_audiobooks_{i}.xml</loc>
  </sitemap>""")

    sitemaps.extend([
        f"""  <sitemap>
    <loc>https://bigear.ru/sitemap_authors.xml</loc>
  </sitemap>""",
        f"""  <sitemap>
    <loc>https://bigear.ru/sitemap_genres.xml</loc>
  </sitemap>""",
        f"""  <sitemap>
    <loc>https://bigear.ru/sitemap_articles.xml</loc>
  </sitemap>"""
    ])

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemaps)}
</sitemapindex>"""

    await cache_set(cache_key, xml_content, ttl=CACHE_TTL)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/sitemap_static.xml")
async def sitemap_static():
    """Sitemap для статических страниц"""
    cache_key = "sitemap_static"
    cached = await cache_get(cache_key)

    if cached:
        return Response(content=cached, media_type="application/xml")

    urls = [
        generate_url_entry("https://bigear.ru/", changefreq="daily", priority="1.0"),
        generate_url_entry("https://bigear.ru/authors", changefreq="weekly", priority="0.9"),
        generate_url_entry("https://bigear.ru/genres", changefreq="weekly", priority="0.9"),
        generate_url_entry("https://bigear.ru/guides/", changefreq="weekly", priority="0.8"),
    ]

    xml_content = wrap_urlset("\n".join(urls))
    await cache_set(cache_key, xml_content, ttl=CACHE_TTL)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/sitemap_audiobooks_{chunk}.xml")
async def sitemap_audiobooks(chunk: int, db: AsyncSession = Depends(get_db)):
    """Sitemap для аудиокниг (по чанкам)"""
    cache_key = f"sitemap_audiobooks_{chunk}"
    cached = await cache_get(cache_key)

    if cached:
        return Response(content=cached, media_type="application/xml")

    offset = (chunk - 1) * CHUNK_SIZE

    result = await db.execute(
        select(Audiobook.slug, Audiobook.updated_at)
        .order_by(Audiobook.id)
        .offset(offset)
        .limit(CHUNK_SIZE)
    )
    audiobooks = result.all()

    urls = []
    for audiobook in audiobooks:
        lastmod = audiobook.updated_at.strftime("%Y-%m-%d") if audiobook.updated_at else None
        urls.append(
            generate_url_entry(
                f"https://bigear.ru/audiobook/{audiobook.slug}",
                lastmod=lastmod,
                changefreq="weekly",
                priority="0.8"
            )
        )

    xml_content = wrap_urlset("\n".join(urls))
    await cache_set(cache_key, xml_content, ttl=CACHE_TTL)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/sitemap_authors.xml")
async def sitemap_authors(db: AsyncSession = Depends(get_db)):
    """Sitemap для авторов"""
    cache_key = "sitemap_authors"
    cached = await cache_get(cache_key)

    if cached:
        return Response(content=cached, media_type="application/xml")

    result = await db.execute(select(Author.slug))
    authors = result.scalars().all()

    urls = [
        generate_url_entry(
            f"https://bigear.ru/author/{author}",
            changefreq="weekly",
            priority="0.7"
        )
        for author in authors
    ]

    xml_content = wrap_urlset("\n".join(urls))
    await cache_set(cache_key, xml_content, ttl=CACHE_TTL)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/sitemap_genres.xml")
async def sitemap_genres(db: AsyncSession = Depends(get_db)):
    """Sitemap для жанров"""
    cache_key = "sitemap_genres"
    cached = await cache_get(cache_key)

    if cached:
        return Response(content=cached, media_type="application/xml")

    result = await db.execute(select(Genre.slug))
    genres = result.scalars().all()

    urls = [
        generate_url_entry(
            f"https://bigear.ru/genre/{genre}",
            changefreq="weekly",
            priority="0.7"
        )
        for genre in genres
    ]

    xml_content = wrap_urlset("\n".join(urls))
    await cache_set(cache_key, xml_content, ttl=CACHE_TTL)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/sitemap_articles.xml")
async def sitemap_articles(db: AsyncSession = Depends(get_db)):
    """Sitemap для статей"""
    cache_key = "sitemap_articles"
    cached = await cache_get(cache_key)

    if cached:
        return Response(content=cached, media_type="application/xml")

    result = await db.execute(select(Guide.slug, Guide.updated_at))
    articles = result.all()

    urls = []
    for article in articles:
        lastmod = article.updated_at.strftime("%Y-%m-%d") if article.updated_at else None
        urls.append(
            generate_url_entry(
                f"https://bigear.ru/guides/{article.slug}",
                lastmod=lastmod,
                changefreq="monthly",
                priority="0.6"
            )
        )

    xml_content = wrap_urlset("\n".join(urls))
    await cache_set(cache_key, xml_content, ttl=CACHE_TTL)
    return Response(content=xml_content, media_type="application/xml")
