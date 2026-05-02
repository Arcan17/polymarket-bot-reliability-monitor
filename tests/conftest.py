"""Pytest fixtures shared across the test suite."""

from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, CheckResult
from app.routers.health import get_db
from config.settings import Settings

# ---------------------------------------------------------------------------
# In-memory SQLite URL used by all test fixtures
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite://"


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Return a Settings instance wired to in-memory SQLite with no Telegram."""
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        TELEGRAM_BOT_TOKEN="",
        TELEGRAM_CHAT_ID="",
        CHECK_INTERVAL_SECONDS=60,
        LOG_LEVEL="DEBUG",
        BINANCE_WS_URL="wss://stream.binance.com:9443/ws/btcusdt@trade",
        CHAINLINK_URL="https://reference-data-directory.vercel.app/feeds-mainnet.json",
        POLYMARKET_URL="https://clob.polymarket.com/markets?limit=1",
    )


@pytest.fixture()
def db_engine():
    """Create a fresh in-memory SQLite engine per test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Generator:
    """Yield a SQLAlchemy session bound to the in-memory test engine."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def test_client(db_engine) -> Generator:
    """Return a FastAPI TestClient with the DB overridden to in-memory SQLite.

    The ``get_db`` dependency is replaced so no real database is needed.
    """
    from app.main import app

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client

    app.dependency_overrides.clear()


def seed_check_result(
    db_session,
    service_name: str = "binance",
    status: str = "ok",
    response_time_ms: float = 42.0,
    error_message: str | None = None,
) -> CheckResult:
    """Helper: insert a CheckResult row and return it."""
    from datetime import datetime

    record = CheckResult(
        service_name=service_name,
        status=status,
        response_time_ms=response_time_ms,
        error_message=error_message,
        checked_at=datetime.utcnow(),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record
