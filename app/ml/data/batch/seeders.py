from datetime import datetime, date as _date, timedelta, timezone
import asyncio

from app.batch.job import Job
from app.batch.models.job_unit import JobUnit
from app.core.db.entity_finder import EntityFinder
from app.core.utils import ftdates
from app.core.utils.logger import get_logger
from app.ml.data.models.daily_agg import DailyAgg
from app.ml.data.models.ticker import Ticker
from app.ml.data.models.sma import SMA
from ..clients.polygon_client import PolygonClient

L = get_logger(__name__)

class SeedTickers(Job):

    def run(self, unit):
        super().run(unit)
        asyncio.run(SeedTickers.seed(unit, self.config))
    
    @staticmethod
    async def seed(unit:JobUnit, conf:dict={}) -> None:
        P = PolygonClient()
        market = conf.get("market")
        if not market:
            raise ValueError("Market must be provided")
        existing_tickers = await Ticker.findAllByMarket(market)
        tickers = await P.getTickerInfo(market)
        ts = datetime.now(timezone.utc)
        to_create = []
        to_update = []
        for obj in tickers:
            T = Ticker(
                ticker=obj.get("ticker"),
                name=obj.get("name"),
                primary_exchange=obj.get("primary_exchange"),
                market=obj.get("market"),
                type=obj.get("type"),
                currency=obj.get("currency_name"),
                active=obj.get("active"),
                last_audit=ts,
                created=ts
            )

            found = None
            for ticker in existing_tickers:
                if T.ticker == ticker.ticker:
                    found = ticker
                    break
            if found is None:
                to_create.append(T)
                unit.accumulate("Tickers created", 1)
            else:
                if not T.equals(found):
                    found.ticker = T.ticker
                    found.name = T.name
                    found.primary_exchange = T.primary_exchange
                    found.market = T.market
                    found.type = T.type
                    found.currency = T.currency
                    found.active = T.active

                    unit.accumulate("Tickers updated", 1)
                found.last_audit = ts
                to_update.append(found)
                unit.accumulate("Tickers audited", 1)

        await EntityFinder.batch_create(to_create)
        await EntityFinder.batch_update(to_update)

        unit.log("Job completed successfully")

class SeedSMA(Job):

    def run(self, unit):
        super().run(unit)
        asyncio.run(SeedSMA.seed(unit, self.config))

    @staticmethod
    async def seed(unit:JobUnit, conf:dict={}) -> None:
        P = PolygonClient()
        _ticker= conf.get("ticker", "all")
        _timespan = conf.get("timespan", "day")
        _window = conf.get("window", 50)
        _series_type = conf.get("series_type", "close")
        _limit = conf.get("limit", 5000)

        tickers = []
        to_create = []
        if _ticker == "all":
            _market = conf.get("market")
            if not _market:
                raise ValueError("Market must be provided if seeding SMA for all tickers")
            tickers = await Ticker.findAllByMarket(_market)
        else:
            _t = await Ticker.findByTicker(_ticker)
            tickers = [_t]
        for ticker in tickers:
            sma = await P.getSMA(ticker=ticker.ticker, timespan=_timespan, window=_window, series_type=_series_type, limit=_limit)

            _existing = await SMA.find_by_ticker(ticker)

            for row in sma.itertuples(index=False):
                _new = SMA(
                    gid_ticker=ticker.gid,
                    value=round(row.value, 4),
                    series_type=_series_type,
                    timespan=_timespan,
                    window=_window,
                    timestamp=datetime.fromtimestamp(row.timestamp / 1000, tz=timezone.utc),
                    date=datetime.fromtimestamp(row.timestamp / 1000, tz=timezone.utc).date()
                )
                exists = False
                for sma in _existing:
                    if _new.equals(sma):
                        exists = True
                        break
                if exists:
                    continue
                to_create.append(_new)
        created = await EntityFinder.batch_create(to_create)
        unit.accumulate("SMA created", created)
        unit.log("Job completed successfully")

class SeedDailyAgg(Job):

    def run(self, unit):
        super().run(unit)
        asyncio.run(SeedDailyAgg.seed(unit, self.config))

    @staticmethod
    async def seed(unit:JobUnit, conf:dict={}) -> None:
        market = conf.get("market")
        ticker = conf.get("ticker")
        max_retries = conf.get("retries", 3)
        end_str = conf.get("end", "1900-01-01")
        start_str = conf.get("start")
        end = ftdates.str_to_date(end_str)
        start = _date.today()
        if start_str:
            start = ftdates.str_to_date(start_str)
        tickers = []
        if (not market and not ticker) or (market and ticker):
            raise Exception("Bad config - params 'ticker' and 'market' are mutually exclusive")
        if not market:
            tickers = [await Ticker.findByTicker(ticker)]
        if not ticker:
            tickers = await Ticker.findAllByMarket(market)
        P = PolygonClient()
        to_create = []
        for ticker in tickers:
            date = ftdates.prev_weekday(start, ticker.primary_exchange)
            retries = max_retries
            aggs = await DailyAgg.find_by_ticker(ticker)
            while retries > 0 and date > end:
                try:
                    existing = False
                    for _agg in aggs:
                        if _agg.date == date:
                            existing = True
                            retries = max_retries
                            break
                    if not existing:
                        agg = await P.getDailyAgg(ticker, date=date)
                        if not agg:
                            retries -= 1
                        else:
                            D = DailyAgg(
                                gid_ticker=ticker.gid,
                                opn=agg["open"],
                                cls=agg["close"],
                                high=agg["high"],
                                low=agg["low"],
                                vol=agg["volume"],
                                date=_date.fromisoformat(agg["date"]),
                                timestamp=datetime.fromtimestamp((datetime.fromordinal(date.toordinal()).timestamp()), tz=timezone.utc)
                            )
                            to_create.append(D)
                            retries = max_retries
                except Exception:
                    L.exception(f"Exception thrown while seeding {ticker.ticker} | {date}")
                    unit.log(f"Exception thrown while seeding {ticker.ticker} | {date}")
                    retries -= 1
                date = ftdates.prev_weekday(date, ticker.primary_exchange)
        created = await EntityFinder.batch_create(to_create)

        unit.accumulate("Daily Agg created", created)
        unit.log("Job completed")