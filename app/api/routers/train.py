from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.batch.models.job_def import JobDef
from app.core.db.session import transaction
from app.core.utils.logger import get_logger
from app.ml.core.models.training_run import TrainingRun
from app.ml.model_defs.model_facade import ModelFacade
from app.ml.training.trainable import Trainable
from ..utils.security import auth
from ...batch.redis_queue import RedisQueue
from ...ml.core.models.model_type import ModelType


# SETUP #
router = APIRouter(
    prefix="/train"
)
L = get_logger(__name__)
# END SETUP #

####################
#      ROUTES      #
####################

class TickerTrainPayload(BaseModel):
    gid_job_def:int
    model_name:str
    config:dict[str, Any]={}

@router.post("/ticker")
@auth
async def post_ticker(payload:TickerTrainPayload) -> JSONResponse:
    async with transaction():
        # Get job instance
        job_def = await JobDef.find_by_gid(payload.gid_job_def)
        _job:Trainable = job_def.get_instance()
        # Get model
        model = await ModelType.find_by_name(payload.model_name)
        # Create training run record
        training_run = await TrainingRun.create(model=model)
        # Configure job
        _job.configure(training_run.gid, payload.config)
        training_run.data = _job.config
        await training_run.update()
        _job.training_run = training_run

        Q = RedisQueue.get_queue("long")
        job = await Q.put(_job)

    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "training_run": {
                    "gid": _job.training_run.gid,
                    "data": _job.training_run.data
                },
                "job_id": f"{job.id}",
                "job_status": f"{job.get_status()}"
            }
        },
        status_code=status.HTTP_202_ACCEPTED
    )