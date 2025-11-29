from typing import Union

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.utils.logger import get_logger
from ..utils.security import auth
from ...batch.redis_queue import RedisQueue
from ...ml.training.simple_price_lstm import Trainer
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
    ticker:str
    epochs:int


@router.post("/{model_name}")
@auth
async def post_(model_name:str, payload:TickerTrainPayload) -> JSONResponse:
    config = {
        "ticker": payload.ticker,
        "epochs": payload.epochs
    }
    model = await ModelType.find_by_name(model_name)
    trainer = model.find_trainer()
    trainer.configure(config=config)

    Q = RedisQueue.get_queue("long")
    job = await Q.put(trainer)

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