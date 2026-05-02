"""Unit tests for the three service checkers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.checkers.binance import BinanceChecker
from app.checkers.chainlink import ChainlinkChecker
from app.checkers.polymarket import PolymarketChecker

# ---------------------------------------------------------------------------
# Binance WebSocket checker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_binance_checker_ok(settings):
    """BinanceChecker returns status='ok' when the WS stream delivers a message."""
    fake_ws = AsyncMock()
    fake_ws.recv = AsyncMock(return_value='{"e":"trade","s":"BTCUSDT"}')
    fake_ws.__aenter__ = AsyncMock(return_value=fake_ws)
    fake_ws.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.binance.websockets.connect", return_value=fake_ws):
        checker = BinanceChecker(settings)
        result = await checker.check()

    assert result.service_name == "binance"
    assert result.status == "ok"
    assert result.response_time_ms is not None
    assert result.error_message is None


@pytest.mark.asyncio
async def test_binance_checker_timeout(settings):
    """BinanceChecker returns status='timeout' when asyncio.wait_for raises TimeoutError."""
    fake_ws = AsyncMock()
    fake_ws.recv = AsyncMock(side_effect=asyncio.TimeoutError())
    fake_ws.__aenter__ = AsyncMock(return_value=fake_ws)
    fake_ws.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.binance.websockets.connect", return_value=fake_ws):
        with patch(
            "app.checkers.binance.asyncio.wait_for", side_effect=asyncio.TimeoutError()
        ):
            checker = BinanceChecker(settings)
            result = await checker.check()

    assert result.service_name == "binance"
    assert result.status == "timeout"
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_binance_checker_error(settings):
    """BinanceChecker returns status='error' on a generic connection exception."""
    fake_ws = AsyncMock()
    fake_ws.__aenter__ = AsyncMock(side_effect=OSError("connection refused"))
    fake_ws.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.binance.websockets.connect", return_value=fake_ws):
        checker = BinanceChecker(settings)
        result = await checker.check()

    assert result.service_name == "binance"
    assert result.status == "error"
    assert "connection refused" in result.error_message


# ---------------------------------------------------------------------------
# Chainlink HTTP checker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chainlink_checker_ok(settings):
    """ChainlinkChecker returns status='ok' for HTTP 200 with a non-empty list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"name": "BTC/USD"}]

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.chainlink.httpx.AsyncClient", return_value=mock_client):
        checker = ChainlinkChecker(settings)
        result = await checker.check()

    assert result.service_name == "chainlink"
    assert result.status == "ok"
    assert result.response_time_ms is not None
    assert result.error_message is None


@pytest.mark.asyncio
async def test_chainlink_checker_error_status(settings):
    """ChainlinkChecker returns status='error' when the server returns HTTP 500."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.chainlink.httpx.AsyncClient", return_value=mock_client):
        checker = ChainlinkChecker(settings)
        result = await checker.check()

    assert result.service_name == "chainlink"
    assert result.status == "error"
    assert "500" in result.error_message


@pytest.mark.asyncio
async def test_chainlink_checker_empty_response(settings):
    """ChainlinkChecker returns status='error' when the response is an empty list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.chainlink.httpx.AsyncClient", return_value=mock_client):
        checker = ChainlinkChecker(settings)
        result = await checker.check()

    assert result.service_name == "chainlink"
    assert result.status == "error"
    assert result.error_message is not None


# ---------------------------------------------------------------------------
# Polymarket HTTP checker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_polymarket_checker_ok(settings):
    """PolymarketChecker returns status='ok' for HTTP 200 with valid JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"id": "abc123"}], "next_cursor": ""}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.polymarket.httpx.AsyncClient", return_value=mock_client):
        checker = PolymarketChecker(settings)
        result = await checker.check()

    assert result.service_name == "polymarket"
    assert result.status == "ok"
    assert result.response_time_ms is not None
    assert result.error_message is None


@pytest.mark.asyncio
async def test_polymarket_checker_error(settings):
    """PolymarketChecker returns status='error' when the server returns HTTP 500."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.polymarket.httpx.AsyncClient", return_value=mock_client):
        checker = PolymarketChecker(settings)
        result = await checker.check()

    assert result.service_name == "polymarket"
    assert result.status == "error"
    assert "500" in result.error_message


@pytest.mark.asyncio
async def test_polymarket_checker_timeout(settings):
    """PolymarketChecker returns status='timeout' on httpx.TimeoutException."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        side_effect=httpx.TimeoutException("timed out", request=None)
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("app.checkers.polymarket.httpx.AsyncClient", return_value=mock_client):
        checker = PolymarketChecker(settings)
        result = await checker.check()

    assert result.service_name == "polymarket"
    assert result.status == "timeout"
    assert result.error_message is not None
