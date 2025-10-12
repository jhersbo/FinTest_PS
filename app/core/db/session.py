from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .db import AsyncSessionLocal

# Chunk size for batch operations
BATCH_CHUNK_SIZE = 1000

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
    finally:
        await session.close()
    """
    return AsyncSessionLocal()

async def query(q: str):
    """
    Runs a single query
    """
    pass

async def batch_create(objects:list[DeclarativeBase]) -> int:
    created = 0
    session = await get_session()
    try:
        async with session.begin():
            payload = []
            for i in range(len(objects)):
                created += 1
                payload.append(objects[i])
                if (i % BATCH_CHUNK_SIZE == 0) or i == len(objects) - 1:
                    session.add_all(payload)
                    payload = []
            await session.commit()
    finally:
        await session.close()

    return created