from fastapi import FastAPI

from app.core.settings import settings

app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url=settings.app.docs_url,
    redoc_url=settings.app.redoc_url,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
