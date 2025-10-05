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

async def batch_create(objects:list[DeclarativeBase]):
    session = await get_session()
    try:
        async with session.begin():
            payload = []
            
            j = 0
            for i in range(len(objects)):
                payload.append(objects[i])
                j += 1
                if j == BATCH_CHUNK_SIZE or i == len(objects) - 1:
                    session.add_all(payload)
                    payload = []
            session.commit()
    finally:
        await session.close()