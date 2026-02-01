from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .db import AsyncSessionLocal, SyncSessionLocal

async def inject_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Used to inject a session instance into an endpoint
    """
    async with AsyncSessionLocal() as session:
        yield session

async def get_session() -> Session:
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

async def query(q: str):
    """
    Runs a single query
    """
    raise NotImplementedError("Function not implemented")


async def batch_create(objects:list):
    raise NotImplementedError()