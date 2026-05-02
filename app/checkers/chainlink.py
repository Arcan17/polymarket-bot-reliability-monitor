"""Chainlink reference-data HTTP availability checker."""

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


class ChainlinkChecker(BaseChecker):
    """Checks Chainlink availability by fetching the reference-data feed list.

    Issues a GET request to the Chainlink reference-data directory endpoint
    and validates that the response is a non-empty JSON list.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialise the checker with application settings.

        Args:
            settings: Application settings containing ``CHAINLINK_URL``.
        """
        self._url = settings.CHAINLINK_URL

    async def check(self) -> CheckResult:
        """Fetch the Chainlink feed list and validate the response.

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
                logger.warning("Chainlink check failed: HTTP %s", response.status_code)
                return CheckResult(
                    service_name="chainlink",
                    status="error",
                    response_time_ms=round(elapsed, 2),
                    error_message=f"HTTP {response.status_code}",
                )

            data = response.json()
            if not isinstance(data, list) or len(data) == 0:
                logger.warning("Chainlink check failed: empty or non-list response")
                return CheckResult(
                    service_name="chainlink",
                    status="error",
                    response_time_ms=round(elapsed, 2),
                    error_message="Response is not a non-empty list",
                )

            logger.debug("Chainlink check ok, %.1f ms", elapsed)
            return CheckResult(
                service_name="chainlink",
                status="ok",
                response_time_ms=round(elapsed, 2),
            )

        except httpx.TimeoutException as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.warning("Chainlink check timed out: %s", exc)
            return CheckResult(
                service_name="chainlink",
                status="timeout",
                response_time_ms=round(elapsed, 2),
                error_message=f"Timed out after {_TIMEOUT_SECONDS}s",
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.warning("Chainlink check error: %s", exc)
            return CheckResult(
                service_name="chainlink",
                status="error",
                response_time_ms=round(elapsed, 2),
                error_message=str(exc),
            )
