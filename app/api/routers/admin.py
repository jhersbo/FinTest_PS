"""
A series of endpoints that are used mostly for testing, but can be used
to trigger daily data processes
"""
import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.utils.logger import get_logger
from ..utils.security import auth
from ...services.data.models.stock_history import StockHistory
from ...services.data.clients.av_client import AVClient
from ...services.data.clients.polygon_client import PolygonClient
from ...services.data.models.stock_tickers  import StockTicker
from ...services.core.models.model_type import ModelType

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
    exist = await StockHistory.find_by_ticker(ticker)
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

        found = False
        for sh in exist:
            if sh.decode == s.decode:
                found = True

        if not found:
            to_create.append(s)
    
    created = await StockHistory.batch_create(to_create)
    return JSONResponse(
        {
            "result": "Ok",
            "subject": f"{created} records created"
        },
        status_code=status.HTTP_201_CREATED
    )

@router.post("/savedata/daily")
@auth
async def post_saveAllDataDaily() -> JSONResponse:

    tickers = await StockTicker.findAll("CS")
    created = 0
    t = 0
    for ticker in tickers:
        # TODO: remove
        L.info(f"{t} of {len(tickers)}")
        t += 1
        ##
        df = None
        try:
            df = await AV.time_series_daily(symbol=ticker, full=True)
        except Exception as e:
            continue
        exist = await StockHistory.find_by_ticker(ticker)
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

            found = False
            for sh in exist:
                if sh.decode == s.decode:
                    found = True

            if not found:
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

@router.post("/seedmodels")
@auth
async def post_seedModels() -> JSONResponse:
    models:list[ModelType] = [
        ModelType(
            model_name="SimplePriceLSTM",
            config={},
            is_available=True
        )
    ]

    created = 0
    updated = 0

    for m in models:
        found = await ModelType.find_by_name(m.model_name)
        if not found:
            await ModelType.create(m.model_name, m.config, m.is_available)
            created += 1
        else:
            if not m.equals(found):
                await m.update()
                updated += 1
    
    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "created": created,
                "updated": updated
            }
        },
        status_code=status.HTTP_201_CREATED
    )