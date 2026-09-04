from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.seed import seed_operational_data
from app.database.session import SessionLocal, init_db
from app.api import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_operational_data(db)
    finally:
        db.close()
    yield


settings = get_settings()
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "message": "AI Emergency Operations Copilot",
        "docs": "/docs",
    }
