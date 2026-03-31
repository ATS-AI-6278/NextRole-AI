import asyncio
import logging
import warnings

# Suppress Python 3.10 deprecation warnings from Google SDK
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core.*")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.telegram.webhook import router as telegram_router
from app.core.config import settings
from app.core.db import engine
from app.memory.relational.repository import init_db
from app.scheduler.digests import start_scheduler

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(title="NextRole AI")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.include_router(telegram_router)

    @app.on_event("startup")
    async def _startup() -> None:
        init_db(engine)
        # MVP: start reporting scheduler immediately.
        start_scheduler()

        # Start Telegram Polling if on localhost or explicitly set.
        if settings.TELEGRAM_POLLING:
            from app.telegram.polling import start_polling
            asyncio.create_task(start_polling())

    return app


app = create_app()
