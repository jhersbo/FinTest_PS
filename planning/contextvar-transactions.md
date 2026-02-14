# ContextVar-Based Implicit Session Propagation

## Context

Model methods use implicit session propagation via a `ContextVar`. The `transaction()` context manager sets a session into the ContextVar, and model methods pick it up automatically via `current_session()`. No `session=` argument passing needed.

This pattern is already proven in the codebase — `app/api/middleware/request_capture.py` uses a `ContextVar[Request]` with `token.set()` / `token.reset()` in exactly the same way.

**Limitation**: ContextVar only works within the async FastAPI context. RQ workers run in separate processes with their own event loops, so sync model methods (`_update`, `start_job`, etc.) continue using their own sessions independently. This is acceptable — RQ worker operations are already isolated.

## Implementation

### 1. `app/core/db/session.py` — ContextVar, `transaction()`, Manual Control

The session module provides:

- **`_current_session` ContextVar** — holds the active `AsyncSession` (or `None`)
- **`current_session()`** — returns the active session, or `None` if outside a `transaction()` block
- **`transaction()`** — async context manager that creates a session, sets the ContextVar, and manages commit/rollback
- **`commit_session()`** — manually commits the current transaction mid-block
- **`rollback_session()`** — manually rolls back the current transaction mid-block

```python
_current_session:ContextVar[Optional[AsyncSession]] = ContextVar("_current_session", default=None)

def current_session() -> Optional[AsyncSession]:
    return _current_session.get(None)

async def rollback_session() -> None:
    session = _current_session.get(None)
    if session is None:
        raise RuntimeError("rollback_session() called outside of a transaction() block")
    await session.rollback()

async def commit_session() -> None:
    session = _current_session.get(None)
    if session is None:
        raise RuntimeError("commit_session() called outside of a transaction() block")
    await session.commit()

@asynccontextmanager
async def transaction() -> AsyncGenerator[AsyncSession, None]:
    existing = _current_session.get(None)
    if existing is not None:
        yield existing          # re-entrant: reuse the existing session
        return

    session = AsyncSessionLocal()
    token = _current_session.set(session)
    try:
        yield session
        if session.in_transaction():
            await session.commit()      # auto-commit on clean exit
    except BaseException:
        if session.in_transaction():
            await session.rollback()    # auto-rollback on exception
        raise
    finally:
        _current_session.reset(token)
        await session.close()
```

**Key design decisions:**

- **No `session.begin()`** — uses SQLAlchemy's implicit transaction (`autocommit=False`). This allows `commit_session()` and `rollback_session()` to be called freely without conflicting with a context manager that owns the transaction lifecycle.
- **`in_transaction()` guards** — prevent errors if a manual commit/rollback already finalized the transaction before block exit.
- **After manual commit/rollback**, SQLAlchemy starts a new implicit transaction automatically. Subsequent work in the block participates in that fresh transaction, which is committed/rolled-back on exit as normal.
- **`RuntimeError` on misuse** — calling `commit_session()` or `rollback_session()` outside a `transaction()` block is a programming error and fails loudly.

### Manual Control Behavior

| Scenario | Result |
|---|---|
| Normal block (no manual calls) | Auto-commits on exit, auto-rolls back on exception |
| `commit_session()` mid-block, then more work | First batch committed permanently, subsequent work committed on exit |
| `rollback_session()` mid-block, then more work | First batch discarded, subsequent work committed on exit |
| `commit_session()` mid-block, then exception | First batch committed permanently, new (empty) txn rolled back |
| Nested re-entrant `commit_session()` | Commits the **entire shared transaction** — no savepoint scoping |
| Called outside `transaction()` | `RuntimeError` raised |

**Caveat**: after `rollback_session()`, previously-loaded ORM objects are expired. Accessing their attributes may trigger lazy loads or return stale data.

### 2. Model methods — Use `transaction()` internally

All async model methods wrap their work in `async with transaction() as session:`. The re-entrant behavior means nested calls reuse the same session automatically — no `session=` parameter passing needed.

**Write pattern** (create/update):
```python
async def create(model_name, ...) -> "ModelType":
    async with transaction() as session:
        gid = await GlobalId.allocate(M)    # re-entrant: reuses same session
        M.gid = gid.gid
        ...
        session.add(M)
        await session.flush()               # flush, not commit — stay in the txn
        return M
```

**Read pattern** (find/query):
```python
async def find_by_gid(gid) -> Optional["ModelType"]:
    async with transaction() as session:
        stmt = select(ModelType).where(ModelType.gid == gid)
        return await session.scalar(statement=stmt)
```

**Batch pattern** (`entity_finder.py`):
```python
async def batch_create(objects) -> int:
    async with transaction() as _session:
        for i, obj in enumerate(objects):
            if isinstance(obj, FindableEntity):
                gid = await GlobalId.allocate(obj)  # re-entrant
                obj.gid = gid.gid
            payload.append(obj)
            if i % BATCH_CHUNK_SIZE == 0 or i == len(objects) - 1:
                _session.add_all(payload)
                await _session.flush()
                payload = []
    return created
```

### 3. Route handlers — Orchestration via outer `transaction()`

Route handlers that need atomicity across multiple model calls open an outer `transaction()` block. All nested model methods re-enter the same session.

**`app/api/routers/admin.py` — atomic upsert**:
```python
async with transaction():
    for m in models:
        found = await ModelType.find_by_name(m.model_name)
        if not found:
            await ModelType.create(...)
        else:
            if not m.equals(found):
                ...
                await found.update()
```

**`app/batch/redis_queue.py` — atomic job creation + enqueue**:
```python
async with transaction():
    unit = await JobUnit.create()
    _job = self.Q.enqueue(job.run, args=(unit,), ...)
    unit.rq_token = _job.id
    await unit.update()
```

Route handlers that call a single model method don't need an explicit `transaction()` — the model method's internal `transaction()` handles it.

## Key Files

| File | Role |
|------|------|
| `app/core/db/session.py` | ContextVar, `transaction()`, `current_session()`, `commit_session()`, `rollback_session()` |
| `app/core/db/db.py` | `AsyncSessionLocal` / `SyncSessionLocal` factory config (`autocommit=False`, `autoflush=False`, `expire_on_commit=False`) |
| `app/core/models/globalid.py` | `allocate()`, `find_by_gid()` — uses `transaction()` internally |
| `app/core/db/entity_finder.py` | `batch_create()`, `batch_update()` — uses `transaction()` with chunked flushing |
| `app/ml/core/models/model_type.py` | `create()`, `update()`, `find_by_gid()`, `find_by_name()` |
| `app/ml/core/models/training_run.py` | `create()`, `update()`, `find_by_id()`, `find_by_model()` (async); `_update()` (sync, RQ workers) |
| `app/batch/models/job_unit.py` | `create()`, `update()`, `find_by_gid()`, `find_by_rqtoken()` (async); `start_job()`, `end_job()`, `fail_job()` (sync, RQ workers) |
| `app/api/routers/admin.py` | Outer `transaction()` for atomic model seeding |
| `app/batch/redis_queue.py` | Outer `transaction()` for atomic job creation + enqueue |

## What is NOT ContextVar-Managed

- **Sync methods** (`_update()`, `start_job`, `end_job`, `fail_job`, `_find_by_gid`) — RQ workers run in separate processes with their own sync sessions via `get_sync_session()` + `session.begin()`
- **`get_session()` / `get_sync_session()`** — standalone session helpers, kept as-is for non-ContextVar usage
