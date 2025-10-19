from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, TIMESTAMP, BOOLEAN, select, update

from ....core.db.session import batch_create, get_session
from ....core.models.entity import Entity

class StockTicker(Entity):
    __tablename__ = "stock_tickers"

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
        String,
        nullable=False
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
    type:Mapped[String] = mapped_column(
        String,
        nullable=False
    )

    @staticmethod
    async def findByTicker(ticker:str) -> "StockTicker":
        """
        Finds StockTicker object by ticker value
        """
        session = await get_session()
        try:
            stmt = select(StockTicker).where(StockTicker.ticker == ticker)
            return await session.scalar(statement=stmt)
        finally:
            await session.close()

    @staticmethod
    async def findAll() -> list["StockTicker"]:
        """
        Finds all tickers
        """
        session = await get_session()
        try:
            stmt = select(StockTicker)
            tups = await session.execute(statement=stmt)
            result = []
            for t in tups:
                result.append(t[0])
            return result
        finally:
            await session.close()

    @staticmethod
    async def create(ticker:str, name:str, currency:str, active:bool=True) -> "StockTicker":
        ts = datetime.now(timezone.utc)
        session = await get_session()
        try:
            S = StockTicker(
                ticker=ticker,
                name=name,
                currency=currency,
                active=active,
                last_audit=ts,
                created=ts
            )
            async with session.begin():
                session.add(S)
            return S
        finally:
            await session.close()

    @staticmethod
    async def batch_create(tickers:list["StockTicker"]) -> int:
        return await batch_create(tickers)
    
    async def update(self) -> None:
        session = await get_session()
        try:
            async with session.begin():
                session.add(self)
        finally:
            await session.close()

    def equals(self, obj:"StockTicker"):
        if type(self) != type(obj):
            return False
        return (
            self.ticker == obj.ticker 
            and self.name == obj.name 
            and self.primary_exchange == obj.primary_exchange 
            and self.currency == obj.currency 
            and self.active == obj.active
        )
        