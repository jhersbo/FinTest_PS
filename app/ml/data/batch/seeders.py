import datetime
import asyncio

from app.batch.job import Job
from app.batch.models.job_unit import JobUnit
from app.core.db.entity_finder import EntityFinder
from app.ml.data.models.ticker import Ticker
from ..clients.polygon_client import PolygonClient


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
            else:
                if not T.equals(found):
                    found.ticker = T.ticker
                    found.name = T.name
                    found.primary_exchange = T.primary_exchange
                    found.market = T.market
                    found.type = T.type
                    found.currency = T.currency
                    found.active = T.active
                found.last_audit = ts
                to_update.append(found)
        
        await EntityFinder.batch_create(to_create)
        await EntityFinder.batch_update(to_update)

        unit.log("Job completed successfully")