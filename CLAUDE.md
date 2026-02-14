# CLAUDE.md

## Project Overview

**FinTest Prediction Service** — stock market prediction platform using LSTM neural networks to forecast financial time series. Manages the full ML lifecycle: data ingestion (via Polygon/AlphaVantage APIs), model training, and prediction. Long-running tasks run as RQ jobs on Redis-backed workers.

## Tech Stack

- **FastAPI** + Uvicorn — async REST API
- **PostgreSQL** via SQLAlchemy async ORM (`asyncpg` driver, `psycopg2` for sync workers)
- **PyTorch** — LSTM models; **scikit-learn** — MinMaxScaler; **joblib** — scaler/metrics serialization
- **Redis** — job queue (RQ) on db=0, rate limiting on db=1
- **pandas** / **numpy** — data manipulation
- **Polygon** / **AlphaVantage** — market data clients (`app/ml/data/clients/`)
- **Python 3.11+**

## Architecture

### Directory Structure
```
app/
├── api/
│   ├── main.py              # FastAPI app, router/middleware registration, exception handlers
│   ├── middleware/           # RateLimiter (Redis sliding window), RequestCapture
│   ├── routers/             # admin, details, predict, train, users, rate_limit
│   └── utils/               # responses.py (WrappedException), security.py (@auth decorator)
├── batch/
│   ├── job.py               # Base Job class (sync run(), async _run())
│   ├── redis_queue.py        # RedisQueue — enqueues jobs, wraps RQ
│   └── models/job_unit.py   # JobUnit — tracks job status, logs, stats
├── core/
│   ├── config/config.py     # EnvConfig (pydantic-settings), get_config()
│   ├── db/
│   │   ├── db.py            # Engine + sessionmaker (async & sync)
│   │   ├── session.py       # ContextVar transaction(), get_session(), get_sync_session()
│   │   └── entity_finder.py # EntityFinder — batch_create/update, dynamic class resolution
│   ├── models/
│   │   ├── entity.py        # Entity, FindableEntity (gid PK), View — base classes
│   │   ├── globalid.py      # GlobalId — auto-increment PK allocation table
│   │   └── token.py         # Token — API auth tokens (x-fintestps-key header)
│   └── utils/               # logger.py (get_logger), ftdates.py (market calendar utils)
└── ml/
    ├── core/models/          # ModelType, TrainingRun
    ├── data/
    │   ├── models/           # Ticker, DailyAgg, SMA, vw_ticker_timeseries (view)
    │   ├── clients/          # PolygonClient, AVClient, client_utils (rate limiting)
    │   └── batch/seeders.py  # SeedTickers, SeedDailyAgg, SeedSMA (Job subclasses)
    ├── model_defs/           # lstm.py (TimeSeriesLSTM nn.Module), model_facade.py
    ├── training/             # Trainable (Job subclass), ts_lstm.py Trainer
    └── prediction/           # Predictable base class, ts_lstm.py Predictor

artifacts/
├── model_output/             # Saved .pth model files (keyed by training run gid)
└── objects/                  # Scaler .pkl + metrics .pkl files
data_files/                   # Local market data CSV/TXT files
planning/                     # Architecture docs, parameter guides
```

### Key Patterns

**1. Job Architecture**
- `Job` → `Trainable` → `ts_lstm.Trainer` (training); `Job` → `SeedTickers`/`SeedDailyAgg`/`SeedSMA` (data ingestion)
- `Job` → `Predictable` → `ts_lstm.Predictor` (prediction — runs inline, not via RQ)
- `RedisQueue.put(job)` creates a `JobUnit`, enqueues `job.run(unit)` in RQ
- RQ workers call sync `run()` which internally uses `asyncio.run()` for async DB operations
- `ModelFacade` resolves trainer/predictor classes dynamically from `ModelType` DB records

**2. Database Layer**
- Three base classes in `entity.py`: `Entity` (no PK), `FindableEntity` (BIGINT `gid` PK), `View` (read-only)
- `GlobalId.allocate(entity)` assigns auto-increment BIGINT primary keys (not UUID)
- `EntityFinder.batch_create()` / `batch_update()` — chunked bulk operations (1000/batch)
- ContextVar `transaction()` context manager (`app/core/db/session.py`):
  - Re-entrant: nested calls yield existing session; outermost caller owns commit/rollback
  - Auto-commits on clean exit, auto-rolls back on exception
  - `commit_session()` / `rollback_session()` for manual mid-block control
  - Write methods use `flush()` to stay within the transaction boundary
  - `expire_on_commit=False` — objects usable after session close
- RQ workers use `get_sync_session()` — separate sync sessions, not ContextVar-managed

**3. API Auth**
- Token-based: `@auth` decorator checks `x-fintestps-key` header against `Token` table
- Tokens created via `POST /users/token`, expire after 90 days
- Rate limiter: Redis sorted set sliding window, 100 req/min per IP, fail-open on Redis error

**4. Training Pipeline** (see [planning/lstm-training-quick-reference.md](planning/lstm-training-quick-reference.md))
- `POST /train/ticker` → creates `TrainingRun`, enqueues `Trainer.run()` via RQ
- Train/val split (temporal, no shuffling), gradient clipping, LR scheduling, early stopping
- Saves: `{gid}.pth` (model), `{gid}_scaler.pkl`, `{gid}_metrics.pkl`

**5. Data Ingestion**
- Seeder jobs fetch from Polygon/AlphaVantage APIs and persist to DB
- `POST /admin/seed/tickers/{market}`, `POST /admin/seed/daily_agg`, `POST /admin/seed/sma`
- Seeders are idempotent — check for existing records before creating

## Code Style

**Conventions**:
- Double-quotes; type hints on signatures; `obj:Type` (no space before colon)
- Modern syntax: `list[str]`, `dict[str, Any]` (not `List`/`Dict`)
- Logging: `L = get_logger(__name__)` at module level
- Response bodies: `{"result":"Ok", "subject":{...}}`

**Naming**:
- PascalCase classes, snake_case functions, UPPER_SNAKE_CASE constants
- Some Ticker queries use camelCase (`findByTicker`, `findAllByMarket`) — legacy pattern

**DB Models**:
- Inherit `FindableEntity` for entities with global IDs, `Entity` for sequence-keyed tables, `View` for views
- Async static methods for queries: `await Model.find_by_gid(gid)`
- Sync prefixed methods for RQ workers: `_find_by_gid()`, `_update()`

**Config**: `get_config()` returns `EnvConfig` (pydantic-settings, reads `.env`)
- Artifact paths: `get_config().mdl_dir`, `get_config().obj_dir`

**ML**: `shuffle=False` for time series; device placement with `model.to(device)` / `tensor.to(device)`
