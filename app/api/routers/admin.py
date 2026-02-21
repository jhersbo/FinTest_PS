"""
A series of endpoints that are used mostly for testing, but can be used
to trigger daily data processes
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rq.exceptions import NoSuchJobError

from app.batch.models.job_def import JobDef
from app.batch.models.job_unit import JobUnit
from app.core.db.session import transaction
from app.core.utils.logger import get_logger
from app.ml.prediction.ts_lstm import Predictor as TSLSTM_Predictor
from app.ml.training.ts_lstm import Trainer as TSLSTM_Trainer
from ..utils.security import auth
from ...ml.data.clients.av_client import AVClient
from ...ml.data.clients.polygon_client import PolygonClient
from ...ml.core.models.model_type import ModelType
from ...ml.data.batch.seeders import SeedDailyAgg, SeedTickers, SeedSMA
from ...ml.data.batch.file_seeders import FileSeedTickers, FileSeedDailyAgg
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

@router.get("/job")
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

@router.get("/jobs")
@auth
async def get_jobList() -> JSONResponse:
    jobs = await JobDef.find_all()
    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "jobs": [
                    job.to_json() for job in jobs
                ]
            }
        }
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

class RunJobPayload(BaseModel):
    gid_job_def:int
    config:dict={}

@router.post("/job/run")
@auth
async def post_runJob(payload:RunJobPayload) -> JSONResponse:
    async with transaction():
        job_def = await JobDef.find_by_gid(payload.gid_job_def)
        _job = job_def.get_instance()
        if payload.config:
            _job.configure(payload.config)

        Q = RedisQueue.get_queue("long")
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

class FileSeedPayload(BaseModel):
    exchange:str = None
    asset_type:str = None
    ticker:str = None
    file_type:str = None

@router.post("/seed/file/tickers")
@auth
async def post_fileSeedTickers(payload:FileSeedPayload) -> JSONResponse:
    config = {
        "exchange": payload.exchange,
        "asset_type": payload.asset_type,
        "ticker": payload.ticker,
        "file_type": payload.file_type
    }
    _job = FileSeedTickers()
    _job.configure(config)

    Q = RedisQueue.get_queue("long")
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

@router.post("/seed/file/daily_agg")
@auth
async def post_fileSeedDailyAgg(payload:FileSeedPayload) -> JSONResponse:
    config = {
        "exchange": payload.exchange,
        "asset_type": payload.asset_type,
        "ticker": payload.ticker,
        "file_type": payload.file_type
    }
    _job = FileSeedDailyAgg()
    _job.configure(config)

    Q = RedisQueue.get_queue("long")
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

@router.post("/seed/jobs")
@auth
async def post_seedJobs() -> JSONResponse:
    jobs:list[JobDef] = [
        JobDef(
            display_name="Train TimeSeries LSTM (default)",
            job_class=TSLSTM_Trainer.get_class_name(),
            default_config={
                "ticker": None,
                "model_type": "TimeSeriesLSTM",
                "f_cols": [],
                "epochs": 100,
                "hidden_size": 64,
                "num_layers": 2,
                "dropout": 0.2,
                "batch_size": 64,
                "learning_rate": 0.001,
                "weight_decay": 1e-5,
                "patience": 15,
                "grad_clip": 1.0,
                "train_split": 0.8
            },
            enabled=True
        ),
        JobDef(
            display_name="Seed Tickers",
            job_class=SeedTickers.get_class_name(),
            default_config={
                "market": None
            },
            enabled=True
        ),
        JobDef(
            display_name="Seed Daily Aggregates",
            job_class=SeedDailyAgg.get_class_name(),
            default_config={
                "ticker": None,
                "market": None,
                "start": None,
                "end": None,
                "retries": 3
            },
            enabled=True
        ),
        JobDef(
            display_name="Seed SMA",
            job_class=SeedSMA.get_class_name(),
            default_config={
                "ticker": "all",
                "market": None,
                "timespan": "day",
                "window": 50,
                "series_type": "close",
                "limit": 5000
            },
            enabled=True
        ),
        JobDef(
            display_name="File Seed Tickers",
            job_class=FileSeedTickers.get_class_name(),
            default_config={
                "exchange": None,
                "asset_type": None,
                "ticker": None,
                "file_type": "txt"
            },
            enabled=True
        ),
        JobDef(
            display_name="File Seed Daily Aggregates",
            job_class=FileSeedDailyAgg.get_class_name(),
            default_config={
                "exchange": None,
                "asset_type": None,
                "ticker": None,
                "file_type": "txt"
            },
            enabled=True
        ),
    ]

    created = 0
    updated = 0

    async with transaction():
        for j in jobs:
            found = await JobDef.find_by_display_name(j.display_name)
            if not found:
                await JobDef.create(j.display_name, j.job_class, j.default_config, j.enabled)
                created += 1
            else:
                if not j.equals(found):
                    found.default_config = j.default_config
                    found.enabled = j.enabled
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

@router.post("/seed/models")
@auth
async def post_seedModels() -> JSONResponse:

    models:list[ModelType] = [
        ModelType(
            model_name="TimeSeriesLSTM",
            is_available=True,
            trainer_name=TSLSTM_Trainer.get_class_name(),
            predictor_name=TSLSTM_Predictor.get_class_name()
        )
    ]

    created = 0
    updated = 0

    async with transaction():
        for m in models:
            found = await ModelType.find_by_name(m.model_name)
            if not found:
                await ModelType.create(m.model_name, m.trainer_name, m.predictor_name, m.is_available)
                created += 1
            else:
                if not m.equals(found):
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