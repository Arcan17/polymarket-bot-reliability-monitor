"""Pydantic v2 schemas for request/response serialisation."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CheckResultSchema(BaseModel):
    """Full representation of a single check result row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    service_name: str
    status: str
    response_time_ms: Optional[float]
    error_message: Optional[str]
    checked_at: datetime


class ServiceSummary(BaseModel):
    """Latest status snapshot for one service."""

    model_config = ConfigDict(from_attributes=True)

    service_name: str
    last_status: str
    last_checked_at: datetime
    last_response_time_ms: Optional[float]


class HealthResponse(BaseModel):
    """Top-level health response returned by GET /health."""

    status: str  # "ok" or "degraded"
    services: List[ServiceSummary]
    timestamp: datetime
