import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings
from app.database import init_db
from app.services.vapi import vapi_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
async def startup():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database ready.")
    if not settings.vapi_api_key:
        logger.warning(
            "VAPI_API_KEY not set — calls will run in simulation mode"
        )


@app.on_event("shutdown")
async def shutdown():
    await vapi_service.close()


@app.get("/health")
async def health():
    return {"status": "ok", "simulation_mode": not bool(settings.vapi_api_key)}
