"""Binance WebSocket availability checker."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

import websockets

from app.checkers.base import BaseChecker, CheckResult

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10


class BinanceChecker(BaseChecker):
    """Checks Binance availability by connecting to their public trade stream.

    Opens a WebSocket connection to the BTC/USDT trade stream, receives a
    single message to confirm the feed is live, then closes the connection.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialise the checker with application settings.

        Args:
            settings: Application settings containing ``BINANCE_WS_URL``.
        """
        self._url = settings.BINANCE_WS_URL

    async def check(self) -> CheckResult:
        """Connect to Binance WebSocket stream and measure latency.

        Returns:
            A :class:`~app.checkers.base.CheckResult` with status ``"ok"``,
            ``"timeout"``, or ``"error"``.
        """
        start = time.monotonic()
        try:
            async with websockets.connect(self._url) as ws:
                await asyncio.wait_for(ws.recv(), timeout=_TIMEOUT_SECONDS)
            elapsed = (time.monotonic() - start) * 1000
            logger.debug("Binance WS check ok, %.1f ms", elapsed)
            return CheckResult(
                service_name="binance",
                status="ok",
                response_time_ms=round(elapsed, 2),
            )
        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start) * 1000
            logger.warning("Binance WS check timed out after %.1f ms", elapsed)
            return CheckResult(
                service_name="binance",
                status="timeout",
                response_time_ms=round(elapsed, 2),
                error_message=f"Timed out after {_TIMEOUT_SECONDS}s",
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            logger.warning("Binance WS check error: %s", exc)
            return CheckResult(
                service_name="binance",
                status="error",
                response_time_ms=round(elapsed, 2),
                error_message=str(exc),
            )
