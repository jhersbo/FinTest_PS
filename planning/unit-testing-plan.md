# Unit Testing Plan — FinTest Prediction Service

## Context

No tests exist in the codebase today. This plan establishes the test infrastructure and a phased approach to unit testing, starting with the easiest wins (pure utilities) and working toward more complex components (ML, API). The goal is incremental coverage that builds confidence without boiling the ocean.

---

## Status

### Infrastructure — ✅ Done
- `tests/` directory structure created (matches plan)
- `pytest.ini` — `asyncio_mode=auto`, `testpaths=tests`, markers `unit`/`slow`
- `tests/conftest.py` — sets all required env vars at module level (before collection) so `logger.py`'s eager `get_config()` call doesn't fail; provisions a `tempfile.mkdtemp()` for `LOG_DIR`
- `requirements-test.txt` — `-r requirements.txt` + test deps; test deps removed from `requirements.txt`
- `Dockerfile.test` — `python:3.11-slim`, installs `requirements-test.txt`, `CMD ["pytest", "tests/unit/", "-v"]`
- `docker-compose.test.yml` — builds from `Dockerfile.test`, mounts `.:/app`, injects stub env vars
- `test.dev.sh` — `./test.dev.sh` runs tests; `./test.dev.sh --build` rebuilds image first
- `.github/workflows/unit_tests.yml` — runs `docker compose -f docker-compose.test.yml run --rm fintest_ps_test`
- `conftest.py` fix: `os.makedirs(os.environ["LOG_DIR"], exist_ok=True)` ensures log dir exists regardless of which path `LOG_DIR` resolves to (local temp dir vs Docker-injected `/tmp/logs`)

> **Key pattern**: ORM objects must be instantiated via the class constructor (e.g. `SampleView(id=1, name="x")`), not `object.__new__()` — the latter skips SQLAlchemy instrumentation init and breaks attribute assignment.

### Phase 1 — ✅ Done (64/64 passing)
| File | Tests | Coverage |
|---|---|---|
| `tests/unit/core/test_ftdates.py` | 26 | `str_to_date`, `today`/`today_minus_days`, `prev_weekday`/`next_weekday` (weekend + holiday skipping), `is_holiday` (US exchange mapping), `is_market_open` (hours, weekend, holiday, boundaries) |
| `tests/unit/core/test_entity.py` | 32 | `_serialize` helper, `Serializable.to_dict`/`to_json`, `View`/`Entity`/`FindableEntity` — `equals`, `repr`, `get_name`, filtering of `_`/`s_id` keys |
| `tests/unit/core/test_config.py` | 6 | `EnvConfig` field loading, missing-field validation error, `get_config()` return types |

---

## 1. Infrastructure Setup

### Directory structure
```
tests/
├── __init__.py
├── conftest.py            # Shared fixtures (mock sessions, fakeredis, sample data)
├── unit/
│   ├── __init__.py
│   ├── core/              # app/core/ tests
│   ├── batch/             # app/batch/ tests
│   ├── ml/                # app/ml/ tests
│   └── api/               # app/api/ tests
└── fixtures/
    ├── __init__.py
    ├── db.py              # Async/sync session mocks
    ├── redis.py           # fakeredis fixtures
    └── sample_data.py     # Reusable test data (configs, tickers, etc.)
```

### Dependencies to add
`pytest`, `pytest-asyncio`, `pytest-mock`, `httpx`, `fakeredis`, `pytest-cov`

### pytest config
- `asyncio_mode = auto`
- Test path: `tests/`
- Markers: `unit`, `slow`

---

## 2. Phased Priorities

### Phase 1 — Core Utilities (pure functions, no mocking needed)
| Module | What to test |
|---|---|
| `app/core/utils/ftdates.py` | Date math, weekday/holiday skipping, market hours, parsing |
| `app/core/models/entity.py` | `to_dict()`, `to_df()`, `equals()` on View/Entity/FindableEntity |
| `app/core/config/config.py` | Config loads from env vars, singleton behavior |

### Phase 2 — Domain Models (mock DB sessions)
| Module | What to test |
|---|---|
| `app/core/models/token.py` | `is_valid()` expiry logic, `create()` UUID generation |
| `app/batch/models/job_unit.py` | State transitions: `start_job` → `end_job`/`fail_job`, `log()`, `stat()`, `accumulate()` |
| `app/ml/core/models/training_run.py` | Status lifecycle (PENDING → RUNNING → COMPLETE/FAILED) |

### Phase 3 — Dynamic Loading & Factories (mock imports)
| Module | What to test |
|---|---|
| `app/core/db/entity_finder.py` | `resolve()` valid/invalid paths, `batch_create()` GID allocation |
| `app/ml/model_defs/model_facade.py` | `trainer_for()`/`predictor_for()` resolve correct classes, `build_config()` merges correctly |

### Phase 4 — Middleware & API Security (fakeredis, mock requests)
| Module | What to test |
|---|---|
| `app/api/middleware/rate_limiter.py` | Sliding window logic, IP extraction, 429 responses, exempt paths, Redis-down fallback |
| `app/api/middleware/request_capture.py` | ContextVar set/get/cleanup |
| `app/api/utils/security.py` | `@auth` decorator: valid/invalid/expired/missing tokens |

### Phase 5 — ML Components (selective, mock heavy)
| Module | What to test |
|---|---|
| `app/ml/model_defs/lstm.py` | `LSTMModel.forward()` — tensor shapes in/out with various hyperparams |
| `app/ml/training/ts_lstm.py` (Dataset) | Sequence generation, scaler fitting, feature column selection |
| `app/batch/redis_queue.py` | `put()` enqueue logic, `find_job()` lookup (mock RQ) |

---

## 3. Mocking Strategy

| Dependency | Approach |
|---|---|
| **Database** | Mock `AsyncSession` / `SyncSession` — patch `get_session()` / `get_sync_session()` |
| **Redis** | `fakeredis.FakeRedis` for rate limiter; mock `rq.Queue` for job queue |
| **External APIs** | Mock `requests.get` / `httpx` for Polygon & Alpha Vantage clients |
| **File system** | Mock `torch.save/load`, `joblib.dump/load` — use `tmp_path` fixture where real files needed |
| **PyTorch training** | Don't run full training loops — test data prep, config, device selection only |
| **Dynamic imports** | Test with real module paths where possible; mock `importlib` for error cases |

---

## 4. Verification

- Run: `pytest tests/unit/ -v`
- Coverage: `pytest --cov=app --cov-report=term-missing tests/unit/`
- Each phase should pass independently before moving to the next
