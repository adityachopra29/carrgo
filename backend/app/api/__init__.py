from fastapi import APIRouter

from app.api.loads import router as loads_router
from app.api.carriers import router as carriers_router
from app.api.campaigns import router as campaigns_router
from app.api.webhooks import router as webhooks_router
from app.api.events import router as events_router

api_router = APIRouter(prefix="/api")
api_router.include_router(loads_router)
api_router.include_router(carriers_router)
api_router.include_router(campaigns_router)
api_router.include_router(webhooks_router)
api_router.include_router(events_router)
