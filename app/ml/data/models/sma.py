from datetime import datetime, timezone
from datetime import date as _date

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, TIMESTAMP, DATE, DOUBLE_PRECISION, INTEGER, BIGINT, select

from app.core.db.session import get_session
from app.core.models.entity import Entity
from app.ml.data.models.ticker import Ticker


class SMA(Entity):
    __tablename__ = "ticker_sma"

    s_id:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False,
        primary_key=True
    )
    gid_ticker:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False
    )
    value:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    series_type:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    timespan:Mapped[String] = mapped_column(
        String,
        nullable=False
    )
    window:Mapped[INTEGER] = mapped_column(
        INTEGER,
        nullable=False
    )
    date:Mapped[DATE] = mapped_column(
        DATE,
        nullable=False
    )
    timestamp:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    @staticmethod
    async def create(ticker:Ticker, value:float, series_type:str, timespan:str, window:int, timestamp:int) -> "SMA":
        ts = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        date = ts.date()
        session = await get_session()
        try:
            S = SMA()
            S.gid_ticker = ticker.gid
            S.value = value
            S.series_type = series_type
            S.timespan = timespan
            S.window = window
            S.date = date
            S.timestamp = ts

            async with session.begin():
                session.add(S)
            return S
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @staticmethod
    async def find_by_ticker(ticker:Ticker) -> list["SMA"]:
        session = await get_session()
        try:
            stmt = select(SMA).where(SMA.gid_ticker==ticker.gid)
            tups = await session.execute(statement=stmt)
            result = []
            for t in tups:
                result.append(t[0])
            return result
        finally:
            await session.close()

    @staticmethod
    async def find_by_ticker_window_date(ticker:Ticker, window:int, date:_date) -> list["SMA"]:
        session = await get_session()
        try:
            stmt = select(SMA).where(
                SMA.gid_ticker==ticker.gid,
                SMA.window==window,
                SMA.date==date
            )
            tups = await session.execute(statement=stmt)
            return [t for t in tups]
        finally:
            await session.close()