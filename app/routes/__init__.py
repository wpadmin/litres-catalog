from fastapi import APIRouter
from app.routes import audiobooks, authors, genres, search, home

router = APIRouter()

router.include_router(home.router, tags=["home"])
router.include_router(audiobooks.router, tags=["audiobooks"])
router.include_router(authors.router, tags=["authors"])
router.include_router(genres.router, tags=["genres"])
router.include_router(search.router, tags=["search"])
