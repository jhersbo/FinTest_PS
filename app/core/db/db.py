import dotenv
import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from ..utils.logger import get_logger
# Logging
L = get_logger(__name__)
# DB CONN SETUP
# DB_URL = dotenv.get_key(".env", "DB_URL") # FOR LOCAL USE
DB_URL = os.environ.get("DB_URL") # FOR DOCKER ENVS
# DB engine
E = create_async_engine(DB_URL, echo=True)
# Session
AsyncSessionLocal = sessionmaker(
    bind=E, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

if __name__ == "__main__":
    async def ping_db():
        try:
            async with E.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                print("✅ Connected! Result:", result.scalar())
        except Exception as e:
            print("❌ Failed to connect:", e)
    asyncio.run(ping_db())