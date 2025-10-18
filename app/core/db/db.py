from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from ..config.config import get_config
from ..utils.logger import get_logger

# Logging
L = get_logger(__name__)
# DB CONN SETUP
DB_URL = get_config().db_url
# DB engine
E = create_async_engine(DB_URL, echo=True)
# Session
AsyncSessionLocal = sessionmaker(
    bind=E, 
    class_=AsyncSession, 
    expire_on_commit=False
)
Base = declarative_base()