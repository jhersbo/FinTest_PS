"""
A series of endpoints that are used mostly for testing, but can be used
to trigger daily data processes
"""
import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import pandas as pd

from app.core.utils.logger import get_logger
from .utils.security import auth
from ...services.models.stock_history import StockHistory
from ...services.clients.av_client import AVClient
from ...services.clients.polygon_client import PolygonClient
from ...services.models.stock_tickers import StockTicker

# SETUP #
router = APIRouter(
    prefix="/admin"
)
L = get_logger(__name__)
# END SETUP #

P = PolygonClient()
AV = AVClient()

####################
#      ROUTES      #
####################
@router.post("/savedata/daily/{ticker}")
@auth
async def post_saveDataDaily(ticker:str) -> JSONResponse:

    df = await AV.time_series_daily(symbol=ticker, full=True)
    to_create = []
    for row in df.itertuples():
        s = StockHistory(
            decode=f"{row.date}|{ticker}",
            date=datetime.date.fromisoformat(row.date),
            ticker=ticker,
            _open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume
        )
        to_create.append(s)
    
    created = await StockHistory.batch_create(to_create)
    return JSONResponse(
        {
            "result": "Ok",
            "subject": f"{created} records created"
        },
        status_code=status.HTTP_201_CREATED
    )

@router.post("/seedtickers/{type}")
@auth
async def post_seedTickers(type:str) -> JSONResponse:
    existing_tickers = await StockTicker.findAll()

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
            type=obj["type"]
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

            await found.update() # TODO - convert to a batch update
    
    created = await StockTicker.batch_create(to_create)
    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "created": created,
                "updated": update_count,
                "audited": audit_count
            }
        },
        status_code=status.HTTP_201_CREATED
    )
    