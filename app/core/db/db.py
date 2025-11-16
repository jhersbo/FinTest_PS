from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from ..config.config import get_config
from ..utils.logger import get_logger

# Logging
L = get_logger(__name__)
# DB CONN SETUP
DB_URL = get_config().db_url
DB_SYNC_URL = get_config().db_sync_url
# DB engine
E = create_async_engine(DB_URL, echo=True)
SE = create_engine(DB_SYNC_URL, echo=True)
# Session - ASYNC
AsyncSessionLocal = sessionmaker(
    bind=E, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)
# Session - SYNC
SyncSessionLocal = sessionmaker(
    bind=SE,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)
# BASE MODEL
Base = declarative_base()