from fastapi import APIRouter

from .routes import router as api_router
from .websockets import router as ws_router

router = APIRouter()
router.include_router(api_router)
router.include_router(ws_router)
