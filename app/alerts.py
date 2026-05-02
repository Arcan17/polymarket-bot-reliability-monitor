"""Alert handling: logs warnings and sends Telegram messages on state transitions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict

from telegram import Bot

from app.checkers.base import CheckResult

if TYPE_CHECKING:
    from config.settings import Settings

logger = logging.getLogger(__name__)

# Maps service_name -> last known status so we can detect ok -> error transitions.
_last_status: Dict[str, str] = {}


async def handle_alert(result: CheckResult, settings: Settings) -> None:
    """Log a warning and optionally send a Telegram alert on state transitions.

    An alert fires when a service transitions from ``"ok"`` to ``"error"`` or
    ``"timeout"``.  The first check after startup does **not** fire an alert
    (no previous state to transition from).

    Args:
        result: The most recent check result for a service.
        settings: Application settings used to resolve Telegram credentials.
    """
    prev = _last_status.get(result.service_name)
    _last_status[result.service_name] = result.status

    if prev == "ok" and result.status in ("error", "timeout"):
        logger.warning(
            "SERVICE DOWN: %s — %s", result.service_name, result.error_message
        )
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            await _send_telegram(result, settings)


async def _send_telegram(result: CheckResult, settings: Settings) -> None:
    """Send a formatted Telegram alert for a service outage.

    Args:
        result: The check result that triggered the alert.
        settings: Application settings containing the bot token and chat id.
    """
    text = (
        "🚨 SERVICE DOWN\n\n"
        f"🔴 {result.service_name}\n"
        f"❌ {result.error_message}\n"
        f"🕐 {result.checked_at.isoformat()}"
    )
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=text)
        logger.info("Telegram alert sent for %s", result.service_name)
    except Exception as exc:
        logger.error("Failed to send Telegram alert: %s", exc)
