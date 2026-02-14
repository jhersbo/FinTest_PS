from app.core.db.session import transaction
from app.core.models.entity import View

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BIGINT, String, TIMESTAMP, BOOLEAN, select, DOUBLE_PRECISION, DATE, INTEGER

from app.ml.data.models.ticker import Ticker


class TickerTimeseries(View):
    __tablename__ = "vw_ticker_timeseries"

    ticker_gid:Mapped[BIGINT] = mapped_column(
        BIGINT,
        primary_key=True
    )
    ticker:Mapped[String] = mapped_column(
        String
    )
    date:Mapped[DATE] = mapped_column(
        DATE
    )
    open:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION
    )
    close:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION
    )
    high:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION
    )
    low:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION
    )
    volume:Mapped[INTEGER] = mapped_column(
        INTEGER
    )
    sma_value:Mapped[DOUBLE_PRECISION] = mapped_column(
        DOUBLE_PRECISION
    )
    sma_series_type:Mapped[String] = mapped_column(
        String,
        primary_key=True
    )
    sma_timespan:Mapped[String] = mapped_column(
        String,
        primary_key=True
    )
    sma_window:Mapped[INTEGER] = mapped_column(
        INTEGER,
        primary_key=True
    )
    sma_date:Mapped[DATE] = mapped_column(
        DATE
    )
    sma_timestamp:Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        primary_key=True
    )

    @staticmethod
    async def findByTicker(
        ticker:Ticker,
        **kwargs
    ) -> list["TickerTimeseries"]:
        async with transaction() as session:
            stmt = select(TickerTimeseries).where(
                TickerTimeseries.ticker_gid==ticker.gid
            ).order_by(TickerTimeseries.date)
            tups = await session.execute(statement=stmt)
            return [t[0] for t in tups]