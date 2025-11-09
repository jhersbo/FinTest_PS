"""
A series of endpoints that are used mostly for testing, but can be used
to trigger daily data processes
"""
import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.utils.logger import get_logger
from ..utils.security import auth
from ...ml.data.models.stock_history import StockHistory
from ...ml.data.clients.av_client import AVClient
from ...ml.data.clients.polygon_client import PolygonClient
from ...ml.data.models.stock_tickers  import StockTicker
from ...ml.core.models.model_type import ModelType
from ...ml.training.simple_price_lstm import Trainer
from ...ml.data.batch.seeders import SeedTickers
from ...batch.redis_queue import RedisQueue

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
    config = {
        "type": type
    }
    job = SeedTickers()
    job.configure(config)

    Q = RedisQueue.get_queue("seeder")
    rj = Q.put(job)

    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "job_status":rj.get_status(),
                "job_id":rj.get_id()
            }
        },
        status_code=status.HTTP_202_ACCEPTED
    )

@router.post("/seedmodels")
@auth
async def post_seedModels() -> JSONResponse:

    models:list[ModelType] = [
        ModelType(
            model_name="SimplePriceLSTM",
            config={},
            is_available=True,
            trainer_name=Trainer().get_class_name()
        )
    ]

    created = 0
    updated = 0

    for m in models:
        found = await ModelType.find_by_name(m.model_name)
        if not found:
            await ModelType.create(m.model_name, m.trainer_name, m.config, m.is_available)
            created += 1
        else:
            if not m.equals(found):
                found.config = m.config
                found.is_available = m.is_available
                found.trainer_name = m.trainer_name
                await found.update()
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