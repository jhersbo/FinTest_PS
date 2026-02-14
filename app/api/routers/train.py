from typing import Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.db.session import transaction
from app.core.utils.logger import get_logger
from app.ml.core.models.training_run import TrainingRun
from app.ml.model_defs.model_facade import ModelFacade
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
    model_name:str
    config:dict[str, Any]

@router.post("/ticker")
@auth
async def post_ticker(payload:TickerTrainPayload) -> JSONResponse:
    model = await ModelType.find_by_name(payload.model_name)
    trainer = ModelFacade.trainer_for(model)

    async with transaction():
        training_run = await TrainingRun.create(model=model)
        config = ModelFacade.build_config(training_run.gid, payload.config, model.default_config)
        training_run.data = config
        await training_run.update()
        
        trainer.configure(config)
        trainer.training_run = training_run

        Q = RedisQueue.get_queue("long")
        job = await Q.put(trainer)

    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "training_run": {
                    "gid": trainer.training_run.gid,
                    "data": trainer.training_run.data
                },
                "job_id": f"{job.id}",
                "job_status": f"{job.get_status()}"
            }
        },
        status_code=status.HTTP_202_ACCEPTED
    )