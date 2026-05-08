# Polymarket Bot Reliability Monitor

![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![CI](https://img.shields.io/github/actions/workflow/status/Arcan17/polymarket-bot-reliability-monitor/ci.yml?label=CI&logo=github)

A standalone production-ready service that continuously monitors the external
infrastructure relied upon by the Polymarket trading bot:

- **Binance** — WebSocket trade stream connectivity
- **Chainlink** — Reference-data HTTP endpoint
- **Polymarket CLOB** — REST API availability

Checks run every 60 seconds (configurable), results are stored in PostgreSQL
(or SQLite for development), and Telegram alerts fire whenever a service
transitions from `ok` to `error`/`timeout`.

---

## Architecture

```
┌─────────────────────────────────────────┐
│          APScheduler (60s)              │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Binance  │ │Chainlink │ │Polym.   │ │
│  │ WS Check │ │HTTP Check│ │HTTP Chk │ │
│  └────┬─────┘ └────┬─────┘ └────┬────┘ │
└───────┼────────────┼────────────┼───────┘
        │            │            │
        └────────────┼────────────┘
                     ▼
              ┌─────────────┐
              │  PostgreSQL │
              │  SQLite     │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  FastAPI    │
              │  REST API   │
              └──────┬──────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      /health    /checks    Telegram
                            Alerts
```

---

## Quickstart

### Docker (recommended)

```bash
# 1. Copy and fill in your environment variables
cp .env.example .env
# Edit .env with your Telegram credentials and preferred DATABASE_URL

# 2. Start everything
docker compose up --build

# 3. API is available at http://localhost:8000
# 4. Interactive docs: http://localhost:8000/docs
```

### Local development (SQLite)

```bash
# 1. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment variables
cp .env.example .env
# Edit .env — you can keep DATABASE_URL=sqlite:///./data/monitor.db for local use

# 4. Run database migrations (optional — init_db() auto-creates tables on startup)
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/monitor.db` | SQLAlchemy connection string |
| `TELEGRAM_BOT_TOKEN` | `` | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | `` | Telegram chat/user ID to send alerts to |
| `CHECK_INTERVAL_SECONDS` | `60` | How often checks run (seconds) |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `BINANCE_WS_URL` | `wss://stream.binance.com:9443/ws/btcusdt@trade` | Binance WebSocket endpoint |
| `CHAINLINK_URL` | `https://reference-data-directory.vercel.app/feeds-mainnet.json` | Chainlink reference data URL |
| `POLYMARKET_URL` | `https://clob.polymarket.com/markets?limit=1` | Polymarket CLOB API URL |

---

## API Reference

### `GET /health`

Returns the overall health status and a per-service summary.

```json
{
  "status": "ok",
  "services": [
    {
      "service_name": "binance",
      "last_status": "ok",
      "last_checked_at": "2026-05-01T12:00:00",
      "last_response_time_ms": 134.5
    }
  ],
  "timestamp": "2026-05-01T12:00:05"
}
```

Overall `status` is `"ok"` when all services are up, `"degraded"` otherwise.

### `GET /checks?limit=50`

Returns the most recent check results across all services (newest first).

### `GET /checks/summary`

Returns one entry per service showing only the latest check result.

### `GET /checks/{service}?limit=20`

Returns recent check results filtered to the specified service name.
Returns an empty list (not 404) for unknown service names.

---

## Running Tests

```bash
# With virtual environment activated:
pytest tests/ -v

# With coverage:
pytest tests/ -v --tb=short
```

The test suite includes 15 tests:

- 9 checker unit tests (Binance, Chainlink, Polymarket — ok/error/timeout paths)
- 6 API integration tests using an in-memory SQLite database
