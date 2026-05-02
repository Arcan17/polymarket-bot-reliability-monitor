"""FastAPI router exposing health and check-history endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import CheckResult, SessionLocal
from app.schemas import CheckResultSchema, HealthResponse, ServiceSummary

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db():
    """FastAPI dependency that yields a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Return the overall health of all monitored services.

    The overall status is ``"ok"`` when all services are up (or no checks
    exist yet) and ``"degraded"`` as soon as any service has a non-``"ok"``
    latest status.

    Args:
        db: Injected database session.

    Returns:
        A :class:`~app.schemas.HealthResponse` with per-service summaries.
    """
    # Fetch latest result per service using a subquery approach
    from sqlalchemy import func

    subq = (
        db.query(
            CheckResult.service_name,
            func.max(CheckResult.checked_at).label("max_checked_at"),
        )
        .group_by(CheckResult.service_name)
        .subquery()
    )

    latest_rows = (
        db.query(CheckResult)
        .join(
            subq,
            (CheckResult.service_name == subq.c.service_name)
            & (CheckResult.checked_at == subq.c.max_checked_at),
        )
        .all()
    )

    summaries: List[ServiceSummary] = [
        ServiceSummary(
            service_name=row.service_name,
            last_status=row.status,
            last_checked_at=row.checked_at,
            last_response_time_ms=row.response_time_ms,
        )
        for row in latest_rows
    ]

    overall = "ok"
    for s in summaries:
        if s.last_status != "ok":
            overall = "degraded"
            break

    return HealthResponse(
        status=overall,
        services=summaries,
        timestamp=datetime.utcnow(),
    )


@router.get("/checks", response_model=List[CheckResultSchema])
def get_checks(limit: int = 50, db: Session = Depends(get_db)) -> List[CheckResult]:
    """Return the most recent check results across all services.

    Args:
        limit: Maximum number of results to return (default 50).
        db: Injected database session.

    Returns:
        List of check results ordered by ``checked_at`` descending.
    """
    return (
        db.query(CheckResult).order_by(desc(CheckResult.checked_at)).limit(limit).all()
    )


@router.get("/checks/summary", response_model=List[ServiceSummary])
def get_checks_summary(db: Session = Depends(get_db)) -> List[ServiceSummary]:
    """Return the latest check result for each monitored service.

    IMPORTANT: This route must be registered **before** ``/checks/{service}``
    to prevent FastAPI from treating ``"summary"`` as a path parameter.

    Args:
        db: Injected database session.

    Returns:
        List of :class:`~app.schemas.ServiceSummary` objects, one per service.
    """
    from sqlalchemy import func

    subq = (
        db.query(
            CheckResult.service_name,
            func.max(CheckResult.checked_at).label("max_checked_at"),
        )
        .group_by(CheckResult.service_name)
        .subquery()
    )

    latest_rows = (
        db.query(CheckResult)
        .join(
            subq,
            (CheckResult.service_name == subq.c.service_name)
            & (CheckResult.checked_at == subq.c.max_checked_at),
        )
        .all()
    )

    return [
        ServiceSummary(
            service_name=row.service_name,
            last_status=row.status,
            last_checked_at=row.checked_at,
            last_response_time_ms=row.response_time_ms,
        )
        for row in latest_rows
    ]


@router.get("/checks/{service}", response_model=List[CheckResultSchema])
def get_checks_by_service(
    service: str, limit: int = 20, db: Session = Depends(get_db)
) -> List[CheckResult]:
    """Return recent check results for a specific service.

    Returns an empty list (not a 404) when the service name is not recognised,
    so callers can handle unknown services gracefully.

    Args:
        service: The service name to filter by (e.g. ``"binance"``).
        limit: Maximum number of results to return (default 20).
        db: Injected database session.

    Returns:
        List of check results for the requested service, newest first.
    """
    return (
        db.query(CheckResult)
        .filter(CheckResult.service_name == service)
        .order_by(desc(CheckResult.checked_at))
        .limit(limit)
        .all()
    )
