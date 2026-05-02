"""FastAPI application entry point with lifespan management."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.checkers.binance import BinanceChecker
from app.checkers.chainlink import ChainlinkChecker
from app.checkers.polymarket import PolymarketChecker
from app.models import SessionLocal, init_db
from app.routers.health import router
from app.scheduler import create_scheduler
from config.settings import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of background services.

    On startup:
    - Initialises database tables.
    - Instantiates the three service checkers.
    - Starts the APScheduler background scheduler.

    On shutdown:
    - Gracefully stops the scheduler.
    """
    logger.info("Starting Polymarket Bot Reliability Monitor")
    init_db()

    checkers = [
        BinanceChecker(settings),
        ChainlinkChecker(settings),
        PolymarketChecker(settings),
    ]

    scheduler = create_scheduler(checkers, SessionLocal, settings)
    scheduler.start()
    logger.info("Scheduler started")

    yield

    logger.info("Shutting down scheduler")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Polymarket Bot Reliability Monitor",
    description=(
        "Monitors the availability of Binance WebSocket, Chainlink HTTP, "
        "and Polymarket CLOB API endpoints used by the Polymarket trading bot."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
