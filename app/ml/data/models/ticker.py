from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, TIMESTAMP, BOOLEAN, select, update

from ....core.models.globalid import GlobalId
from ....core.db.session import batch_create, get_session
from ....core.models.entity import FindableEntity

class Ticker(FindableEntity):
    __tablename__ = "core_ticker"
    __name__ = f"{__name__}.Ticker"

    ticker:Mapped[String] = mapped_column(
        String,
        nullable=False,
        primary_key=True
    )
    name:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    primary_exchange:Mapped[String] = mapped_column(
        String
    )
    market:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    type:Mapped[String] = mapped_column(
        String
    )
    currency:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    active:Mapped[BOOLEAN] = mapped_column(
        BOOLEAN,
        nullable=False
    )
    last_audit:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )
    created:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    @staticmethod
    async def findByTicker(ticker:str) -> "Ticker":
        """
        Finds Ticker object by ticker value
        """
        session = await get_session()
        try:
            stmt = select(Ticker).where(Ticker.ticker == ticker)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()

    @staticmethod
    async def findAll() -> list["Ticker"]:
        """
        Finds all tickers
        """
        session = await get_session()
        try:
            stmt = select(Ticker)
            tups = await session.execute(statement=stmt)
            result = []
            for t in tups:
                result.append(t[0])
            return result
        finally:
            await session.close()

    @staticmethod
    async def findAllByMarket(market:str) -> list["Ticker"]:
        session = await get_session()
        try:
            stmt = select(Ticker).where(Ticker.market == market)
            tups = await session.execute(statement=stmt)
            result = []
            for t in tups:
                result.append(t[0])
            return result
        finally:
            await session.close()

    @staticmethod
    async def create(ticker:str, name:str, primary_exchange:str, currency:str, type:str, market:str, active:bool=True) -> "Ticker":
        ts = datetime.now(timezone.utc)
        session = await get_session()
        try:

            T = Ticker()
            gid = await GlobalId.allocate(T)

            T.gid = gid.gid
            T.ticker = ticker
            T.name = name
            T.primary_exchange = primary_exchange
            T.currency = currency
            T.type = type
            T.market = market
            T.active = active
            T.last_audit = ts
            T.created = ts

            async with session.begin():
                session.add(T)
            return T
        finally:
            await session.close()

    @staticmethod
    async def batch_create(tickers:list["Ticker"]) -> int:
        return await batch_create(tickers)
    
    async def update(self) -> None:
        session = await get_session()
        try:
            async with session.begin():
                session.add(self)
        finally:
            await session.close()
        