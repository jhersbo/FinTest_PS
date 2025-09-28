from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from .db import AsyncSessionLocal

async def inject_db() -> AsyncGenerator[AsyncSession, None]:
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