"""Application settings loaded from environment variables via python-decouple."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from decouple import config


@dataclass
class Settings:
    """All application configuration in one place."""

    DATABASE_URL: str
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    CHECK_INTERVAL_SECONDS: int
    LOG_LEVEL: str
    BINANCE_WS_URL: str
    CHAINLINK_URL: str
    POLYMARKET_URL: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance loaded from environment variables.

    Uses python-decouple to read values from .env or the real environment.
    Safe defaults are provided for every field so the app starts without a
    .env file (useful in CI / tests).
    """
    return Settings(
        DATABASE_URL=config("DATABASE_URL", default="sqlite:///./data/monitor.db"),
        TELEGRAM_BOT_TOKEN=config("TELEGRAM_BOT_TOKEN", default=""),
        TELEGRAM_CHAT_ID=config("TELEGRAM_CHAT_ID", default=""),
        CHECK_INTERVAL_SECONDS=config("CHECK_INTERVAL_SECONDS", default=60, cast=int),
        LOG_LEVEL=config("LOG_LEVEL", default="INFO"),
        BINANCE_WS_URL=config(
            "BINANCE_WS_URL",
            default="wss://stream.binance.com:9443/ws/btcusdt@trade",
        ),
        CHAINLINK_URL=config(
            "CHAINLINK_URL",
            default="https://reference-data-directory.vercel.app/feeds-mainnet.json",
        ),
        POLYMARKET_URL=config(
            "POLYMARKET_URL",
            default="https://clob.polymarket.com/markets?limit=1",
        ),
    )
