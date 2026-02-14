from contextvars import ContextVar
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .db import AsyncSessionLocal, SyncSessionLocal

_current_session:ContextVar[Optional[AsyncSession]] = ContextVar("_current_session", default=None)

def current_session() -> Optional[AsyncSession]:
    """Returns the active transaction session, or None if not in a transaction() block."""
    return _current_session.get(None)

async def rollback_session() -> None:
    """
    Rolls back the current transaction within a transaction() block.

    After rollback, a new implicit transaction begins automatically.
    Subsequent operations in the same block participate in the fresh transaction.
    Previously-loaded ORM objects will be expired.
    """
    session = _current_session.get(None)
    if session is None:
        raise RuntimeError("rollback_session() called outside of a transaction() block")
    await session.rollback()

async def commit_session() -> None:
    """
    Commits the current transaction within a transaction() block.

    After commit, a new implicit transaction begins automatically.
    Subsequent operations in the same block participate in the fresh transaction.
    Committed data is durable and will not be rolled back by later failures.
    """
    session = _current_session.get(None)
    if session is None:
        raise RuntimeError("commit_session() called outside of a transaction() block")
    await session.commit()

@asynccontextmanager
async def transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that creates a session, sets it into the ContextVar,
    and wraps the body in a database transaction.

    Re-entrant: if already inside a transaction(), yields the existing session
    without creating a nested transaction. The outermost caller owns commit/rollback.

    On clean exit: auto-commits any pending work.
    On exception: auto-rolls back any pending work, then re-raises.

    Manual control: commit_session() and rollback_session() may be called within the
    block. After either call, a new implicit transaction begins automatically, so
    subsequent work is committed/rolled-back independently on exit.
    """
    existing = _current_session.get(None)
    if existing is not None:
        yield existing
        return

    session = AsyncSessionLocal()
    token = _current_session.set(session)
    try:
        yield session
        if session.in_transaction():
            await session.commit()
    except BaseException:
        if session.in_transaction():
            await session.rollback()
        raise
    finally:
        _current_session.reset(token)
        await session.close()

async def inject_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Used to inject a session instance into an endpoint
    """
    async with AsyncSessionLocal() as session:
        yield session

async def get_session() -> AsyncSession:
    """
    Returns a session instance. Calling functions are responsible
    for closing the session when done.

    Example:
    ```python
    session = await get_session()
    try:
        return await session.execute(...)
    except:
        await session.rollback()
        raise
    finally:
        await session.close()
    """
    return AsyncSessionLocal()

def get_sync_session() -> Session:
    """
    Returns a session instance. Calling functions are responsible
    for closing the session when done.

    Example:
    ```python
    session = get_sync_session()
    try:
        return session.execute(...)
    except:
        session.rollback()
        raise
    finally:
        session.close()
    """
    return SyncSessionLocal()