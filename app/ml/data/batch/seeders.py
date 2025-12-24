import datetime
import asyncio

from app.batch.job import Job
from app.batch.models.job_unit import JobUnit
from app.core.db.entity_finder import EntityFinder
from app.core.utils.logger import get_logger
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
        ts = datetime.datetime.now(datetime.timezone.utc)
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
                    value=row.value,
                    series_type=_series_type,
                    timespan=_timespan,
                    window=_window,
                    timestamp=datetime.datetime.fromtimestamp(row.timestamp / 1000, tz=datetime.timezone.utc),
                    date=datetime.datetime.fromtimestamp(row.timestamp / 1000, tz=datetime.timezone.utc).date()
                )
                # TODO - need to figure out a way to better compare them
                if _new.equals(_existing):
                    continue
                to_create.append(_new)

        print(len(to_create))

        # created = await EntityFinder.batch_create(to_create)
        # unit.accumulate("SMA created", created)

        unit.log("Job completed successfully")