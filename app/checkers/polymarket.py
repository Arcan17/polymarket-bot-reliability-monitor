"""Polymarket CLOB HTTP availability checker."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import httpx

from app.checkers.base import BaseChecker, CheckResult

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10


class PolymarketChecker(BaseChecker):
    """Checks Polymarket CLOB API availability by fetching the markets endpoint.

    Issues a GET request to the Polymarket CLOB markets endpoint and validates
    that the response is a successful HTTP 200 with valid JSON.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialise the checker with application settings.

        Args:
            settings: Application settings containing ``POLYMARKET_URL``.
        """
        self._url = settings.POLYMARKET_URL

    async def check(self) -> CheckResult:
        """Fetch the Polymarket markets endpoint and validate the response.

        Returns:
            A :class:`~app.checkers.base.CheckResult` with status ``"ok"``,
            ``"timeout"``, or ``"error"``.
        """
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.get(self._url)
            elapsed = (time.monotonic() - start) * 1000

            if response.status_code != 200:
                logger.warning("Polymarket check failed: HTTP %s", response.status_code)
                return CheckResult(
                    service_name="polymarket",
                    status="error",
                    response_time_ms=round(elapsed, 2),
                    error_message=f"HTTP {response.status_code}",
                )

            # Validate JSON is parseable
            response.json()

            logger.debug("Polymarket check ok, %.1f ms", elapsed)
            return CheckResult(
                service_name="polymarket",
                status="ok",
                response_time_ms=round(elapsed, 2),
            )

        except httpx.TimeoutException as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.warning("Polymarket check timed out: %s", exc)
            return CheckResult(
                service_name="polymarket",
                status="timeout",
                response_time_ms=round(elapsed, 2),
                error_message=f"Timed out after {_TIMEOUT_SECONDS}s",
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.warning("Polymarket check error: %s", exc)
            return CheckResult(
                service_name="polymarket",
                status="error",
                response_time_ms=round(elapsed, 2),
                error_message=str(exc),
            )
