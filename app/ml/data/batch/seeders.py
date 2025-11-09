import datetime
import asyncio

from app.batch.job import Job
from app.ml.data.models.stock_tickers import StockTicker
from ..clients.polygon_client import PolygonClient


class SeedTickers(Job):

    def run(self) -> None:
        return asyncio.run(SeedTickers.seed(self.config))
    
    @staticmethod
    async def seed(conf:dict={}) -> None:
        P = PolygonClient()
        type = conf.get("type")
        if not type:
            raise ValueError("Type must be provided")

        existing_tickers = await StockTicker.findAll("CS")
        tickers = await P.getTickerInfo(type)
        ts = datetime.datetime.now(datetime.timezone.utc)
        to_create = []
        update_count = 0
        audit_count = 0
        for obj in tickers:
            T = StockTicker(
                ticker=obj["ticker"],
                name=obj["name"],
                primary_exchange=obj["primary_exchange"],
                currency=obj["currency_name"],
                active=obj["active"],
                last_audit=ts,
                created=ts,
                type=type
            )

            found = None
            for i, ex in enumerate(existing_tickers):
                if T.ticker == ex.ticker:
                    found = existing_tickers[i]
                    break
            if found is None:
                to_create.append(T)
            else:
                if not T.equals(found):
                    found.ticker = T.ticker
                    found.name = T.name
                    found.primary_exchange = T.primary_exchange
                    found.currency = T.currency
                    found.active = T.active

                    update_count += 1
                found.last_audit = ts
                audit_count += 1

                await found.update()
        
        created = await StockTicker.batch_create(to_create)