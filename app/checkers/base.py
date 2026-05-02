"""Base checker dataclass and abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CheckResult:
    """Holds the outcome of a single service availability check.

    Attributes:
        service_name: Identifies which service was checked.
        status: One of ``"ok"``, ``"error"``, or ``"timeout"``.
        response_time_ms: Round-trip time in milliseconds, or ``None`` when
            the check did not reach the service successfully.
        error_message: Human-readable description of what went wrong, or
            ``None`` on success.
        checked_at: UTC timestamp of when the check was executed.
    """

    service_name: str
    status: str  # "ok", "error", "timeout"
    response_time_ms: Optional[float]
    error_message: Optional[str] = None
    checked_at: datetime = field(default_factory=lambda: datetime.utcnow())


class BaseChecker(ABC):
    """Abstract base class that every service checker must implement."""

    @abstractmethod
    async def check(self) -> CheckResult:
        """Perform the service check and return a :class:`CheckResult`.

        Implementations must be async and must never raise unhandled
        exceptions — all errors should be captured and reflected in the
        returned :class:`CheckResult`.
        """
        ...
