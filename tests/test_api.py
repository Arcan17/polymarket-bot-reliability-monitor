"""Integration tests for the FastAPI REST endpoints."""

from __future__ import annotations

from tests.conftest import seed_check_result

# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


def test_health_endpoint_empty_db(test_client):
    """GET /health with no check data returns overall status='ok'."""
    response = test_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["services"] == []
    assert "timestamp" in body


def test_health_endpoint_with_data(test_client, db_session):
    """GET /health reflects seeded check results correctly."""
    seed_check_result(db_session, service_name="binance", status="ok")
    seed_check_result(
        db_session, service_name="chainlink", status="error", error_message="HTTP 500"
    )

    response = test_client.get("/health")
    assert response.status_code == 200
    body = response.json()

    # At least one service is in error → overall degraded
    assert body["status"] == "degraded"
    service_names = {s["service_name"] for s in body["services"]}
    assert "binance" in service_names
    assert "chainlink" in service_names

    chainlink_summary = next(
        s for s in body["services"] if s["service_name"] == "chainlink"
    )
    assert chainlink_summary["last_status"] == "error"


# ---------------------------------------------------------------------------
# GET /checks
# ---------------------------------------------------------------------------


def test_checks_endpoint(test_client, db_session):
    """GET /checks returns a list of check results ordered newest first."""
    seed_check_result(db_session, service_name="binance", status="ok")
    seed_check_result(db_session, service_name="polymarket", status="ok")

    response = test_client.get("/checks")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 2
    # Each item must have the expected fields
    for item in body:
        assert "service_name" in item
        assert "status" in item
        assert "checked_at" in item


def test_checks_endpoint_limit(test_client, db_session):
    """GET /checks?limit=1 returns at most 1 result."""
    seed_check_result(db_session, service_name="binance", status="ok")
    seed_check_result(db_session, service_name="chainlink", status="ok")

    response = test_client.get("/checks?limit=1")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1


# ---------------------------------------------------------------------------
# GET /checks/summary
# ---------------------------------------------------------------------------


def test_checks_summary_endpoint(test_client, db_session):
    """GET /checks/summary returns one entry per service with the latest status."""
    seed_check_result(db_session, service_name="binance", status="error")
    seed_check_result(db_session, service_name="binance", status="ok")  # latest
    seed_check_result(db_session, service_name="polymarket", status="ok")

    response = test_client.get("/checks/summary")
    assert response.status_code == 200
    body = response.json()

    assert isinstance(body, list)
    binance_entry = next((s for s in body if s["service_name"] == "binance"), None)
    assert binance_entry is not None
    # Should reflect the most recent result
    assert binance_entry["last_status"] == "ok"


# ---------------------------------------------------------------------------
# GET /checks/{service}
# ---------------------------------------------------------------------------


def test_checks_by_service_endpoint(test_client, db_session):
    """GET /checks/binance returns only binance results."""
    seed_check_result(db_session, service_name="binance", status="ok")
    seed_check_result(db_session, service_name="chainlink", status="ok")

    response = test_client.get("/checks/binance")
    assert response.status_code == 200
    body = response.json()

    assert isinstance(body, list)
    assert len(body) >= 1
    for item in body:
        assert item["service_name"] == "binance"


def test_checks_by_unknown_service(test_client):
    """GET /checks/unknown returns an empty list, not a 404."""
    response = test_client.get("/checks/unknown_service_xyz")
    assert response.status_code == 200
    body = response.json()
    assert body == []
