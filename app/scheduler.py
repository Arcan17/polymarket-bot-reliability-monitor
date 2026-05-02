"""APScheduler setup and the periodic check runner."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.alerts import handle_alert
from app.checkers.base import BaseChecker
from app.models import CheckResult as CheckResultModel

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)


def create_scheduler(
    checkers: List[BaseChecker],
    session_factory,
    settings: Settings,
) -> AsyncIOScheduler:
    """Create and configure an :class:`AsyncIOScheduler`.

    The scheduler will run :func:`run_all_checks` every
    ``settings.CHECK_INTERVAL_SECONDS`` seconds.

    Args:
        checkers: List of :class:`~app.checkers.base.BaseChecker` instances.
        session_factory: A SQLAlchemy ``sessionmaker`` used to open DB sessions.
        settings: Application settings (provides the check interval).

    Returns:
        A configured but **not yet started** :class:`AsyncIOScheduler`.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_all_checks,
        "interval",
        seconds=settings.CHECK_INTERVAL_SECONDS,
        args=[checkers, session_factory, settings],
        id="run_all_checks",
        replace_existing=True,
    )
    logger.info(
        "Scheduler configured: %d checker(s), interval=%ds",
        len(checkers),
        settings.CHECK_INTERVAL_SECONDS,
    )
    return scheduler


async def run_all_checks(
    checkers: List[BaseChecker],
    session_factory,
    settings: Settings,
) -> None:
    """Execute all registered checkers and persist results to the database.

    For each checker the result is saved to the database and then passed to
    :func:`~app.alerts.handle_alert` to trigger notifications when needed.

    Args:
        checkers: List of checker instances to run.
        session_factory: SQLAlchemy ``sessionmaker`` for DB access.
        settings: Application settings forwarded to alert handling.
    """
    for checker in checkers:
        try:
            result = await checker.check()
        except Exception as exc:
            logger.error("Unhandled exception in checker %s: %s", checker, exc)
            continue

        # Persist to database
        db = session_factory()
        try:
            db_record = CheckResultModel(
                service_name=result.service_name,
                status=result.status,
                response_time_ms=result.response_time_ms,
                error_message=result.error_message,
                checked_at=result.checked_at,
            )
            db.add(db_record)
            db.commit()
        except Exception as exc:
            logger.error(
                "Failed to persist check result for %s: %s", result.service_name, exc
            )
            db.rollback()
        finally:
            db.close()

        # Fire alerts if state changed
        try:
            await handle_alert(result, settings)
        except Exception as exc:
            logger.error("handle_alert raised for %s: %s", result.service_name, exc)
