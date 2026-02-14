from datetime import datetime, date as _date, timezone

from sqlalchemy import BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TIMESTAMP, DATE, DOUBLE_PRECISION, INTEGER, BIGINT, select

from app.core.db.session import transaction
from app.core.models.entity import Entity
from app.ml.data.models.ticker import Ticker


class DailyAgg(Entity):
    __tablename__ = "ticker_dailyagg"

    s_id:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False,
        primary_key=True
    )
    gid_ticker:Mapped[BIGINT] = mapped_column(
        BIGINT,
        nullable=False
    )
    opn:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    cls:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    high:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    low:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION,
        nullable=False
    )
    vol:Mapped[DOUBLE_PRECISION] = mapped_column(
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
    async def create(
        ticker:Ticker,
        opn:float,
        cls:float,
        high:float,
        low:float,
        vol:int,
        date:_date,
        timestamp:int
    ) -> "DailyAgg":
        dt = datetime.fromtimestamp((timestamp if timestamp else datetime.fromordinal(date.toordinal()).timestamp()), tz=timezone.utc)
        D = DailyAgg()
        D.gid_ticker = ticker.gid
        D.opn = opn
        D.cls = cls
        D.high = high
        D.low = low
        D.vol = vol
        D.date = date
        D.timestamp = dt

        async with transaction() as session:
            session.add(D)
            await session.flush()
            return D

    @staticmethod
    async def find_by_ticker_date(ticker:Ticker, date:_date) -> "DailyAgg":
        async with transaction() as session:
            stmt = select(DailyAgg).where(
                DailyAgg.gid_ticker==ticker.gid,
                DailyAgg.date==date
            )
            return await session.scalar(statement=stmt)

    @staticmethod
    async def find_by_ticker(ticker:Ticker) -> list["DailyAgg"]:
        async with transaction() as session:
            stmt = select(DailyAgg).where(
                DailyAgg.gid_ticker==ticker.gid
            )
            tups = await session.execute(statement=stmt)
            return [t[0] for t in tups]