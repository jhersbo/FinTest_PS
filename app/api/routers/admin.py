"""
A series of endpoints that are used mostly for testing, but can be used
to trigger daily data processes
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rq.exceptions import NoSuchJobError

from app.batch.models.job_unit import JobUnit
from app.core.utils.logger import get_logger
from app.ml.prediction.ts_lstm import Predictor as TSLSTM_Predictor
from app.ml.training.ts_lstm import Trainer as TSLSTM_Trainer
from ..utils.security import auth
from ...ml.data.clients.av_client import AVClient
from ...ml.data.clients.polygon_client import PolygonClient
from ...ml.core.models.model_type import ModelType
from ...ml.training.simple_price_lstm import Trainer as SPLSTM_Trainer
from app.ml.prediction.simple_price_lstm import Predictor as SPLSTM_Predictor
from ...ml.data.batch.seeders import SeedDailyAgg, SeedTickers, SeedSMA
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

@router.get("/job/{rq_token}")
@auth
async def get_job(rq_token:str) -> JSONResponse:
    job = None
    try:
        job = RedisQueue.find_job(rq_token)
        return JSONResponse(
            {
                "result": "Ok",
                "subject":{
                    "job": {
                        "id": job.id,
                        "status": job.get_status(),
                        "meta": job.get_meta()
                    }
                }
            },
            status_code=status.HTTP_200_OK
        )
    except NoSuchJobError:
        L.exception("No such job")

    return JSONResponse(
        {
            "result": "Ok",
            "subject":{
                "job": None
            }
        },
        status_code=status.HTTP_200_OK
    )

@router.post("/seed/tickers/{market}")
@auth
async def post_seedTickers(market:str) -> JSONResponse:
    config = {
        "market": market
    }
    job = SeedTickers()
    job.configure(config)

    Q = RedisQueue.get_queue("long")
    rj = await Q.put(job)

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

class SeedDailyAggPayload(BaseModel):
    """
    ticker - if seeding a single ticker, define ticker\n
    market - if seeing all tickers for a market type, define market\n
    start - date to start counting backwards from\n
    end - date to conclude\n
    retries - how many retries the job is allowed
    """
    ticker:str=None
    market:str=None
    start:str=None
    end:str=None
    retries:int=None

@router.post("/seed/daily_agg")
@auth
async def post_seedDailyAgg(payload:SeedDailyAggPayload) -> JSONResponse:
    config = {
        "ticker": payload.ticker,
        "market": payload.market,
        "start": payload.start,
        "end": payload.end,
        "retries": payload.retries
    }
    _job = SeedDailyAgg()
    _job.configure(config)

    Q = RedisQueue.get_queue("long")
    job = await Q.put(_job)
    job_unit = await JobUnit.find_by_rqtoken(job.id)

    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                # "job_unit": job_unit.gid,
                "job_id": f"{job.id}",
                "job_status": f"{job.get_status()}"
            }
        },
        status_code=status.HTTP_202_ACCEPTED
    )


class SeedSMAPayload(BaseModel):
    ticker:str=None
    market:str=None
    timespan:str=None
    window:int=None
    series_type:str=None
    limit:int=None

@router.post("/seed/sma")
@auth
async def post_seedSMA(payload:SeedSMAPayload) -> JSONResponse:
    config = {
        "ticker": payload.ticker,
        "market": payload.market,
        "timespan": payload.timespan,
        "window": payload.window,
        "series_type": payload.series_type,
        "limit": payload.limit
    }

    _job = SeedSMA()
    _job.configure(config)

    Q = RedisQueue.get_queue("short")
    job = await Q.put(_job)

    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "job_id": f"{job.id}",
                "job_status": f"{job.get_status()}"
            }
        },
        status_code=status.HTTP_202_ACCEPTED
    )


@router.post("/seed/models")
@auth
async def post_seedModels() -> JSONResponse:

    models:list[ModelType] = [
        ModelType(
            model_name="SimplePriceLSTM",
            is_available=True,
            trainer_name=SPLSTM_Trainer().get_class_name(),
            predictor_name=SPLSTM_Predictor().get_class_name(),
            default_config={}
        ),
        ModelType(
            model_name="TimeSeriesLSTM",
            is_available=True,
            trainer_name=TSLSTM_Trainer().get_class_name(),
            predictor_name=TSLSTM_Predictor().get_class_name(),
            default_config={
                "ticker": "",
                "f_cols": [],
                "epochs":100,
                "hidden_size":64,
                "num_layers":2,
                "dropout":0.2,
                "batch_size":64,
                "learing_rate":0.001,
                "weight_decay":1e-5,
                "patience":15,
                "grad_clip":1.0,
                "train_split":0.8
            }
        )
    ]

    created = 0
    updated = 0

    for m in models:
        found = await ModelType.find_by_name(m.model_name)
        if not found:
            await ModelType.create(m.model_name, m.trainer_name, m.predictor_name, m.default_config, m.is_available)
            created += 1
        else:
            if not m.equals(found):
                found.config = m.config
                found.is_available = m.is_available
                found.trainer_name = m.trainer_name
                found.predictor_name = m.predictor_name
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