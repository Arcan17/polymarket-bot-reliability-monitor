"""SQLAlchemy ORM models and database engine setup."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from config.settings import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


class CheckResult(Base):
    """Stores the result of a single service availability check.

    Each row represents one check of one service at one point in time.
    """

    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "ok", "error", "timeout"
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


def _build_engine():
    """Build the SQLAlchemy engine from settings.

    SQLite databases use check_same_thread=False so that the engine can be
    shared across threads/async tasks without errors.
    """
    settings = get_settings()
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.DATABASE_URL, connect_args=connect_args)


engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they do not already exist.

    This is a lightweight alternative to running Alembic migrations and is
    used inside the FastAPI lifespan for development / SQLite mode.  In
    production with PostgreSQL, run ``alembic upgrade head`` instead.
    """
    logger.info("Initialising database tables")
    Base.metadata.create_all(bind=engine)
