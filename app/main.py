from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.site_name}...")
    yield
    print("Stopping application...")


app = FastAPI(
    title=settings.site_name,
    description=settings.site_description,
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.site_name}
