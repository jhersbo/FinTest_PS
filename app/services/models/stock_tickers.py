from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, TIMESTAMP, BOOLEAN

from ...core.db.session import batch_create, get_session
from ...core.models.entity import Entity

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