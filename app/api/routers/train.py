from typing import Union

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.utils.logger import get_logger
from ..utils.security import auth
from ..utils.responses import WrappedException
from ...batch.queue import RedisQueue
from ...ml.training.simple_price_lstm import Trainer


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
    ticker:str
    epochs:int


@router.post("/")
@auth
async def post_(payload:TickerTrainPayload) -> JSONResponse:
    config = {
        "ticker": payload.ticker,
        "epochs": payload.epochs
    }
    job_class = Trainer()
    job_class.configure(config)

    Q = RedisQueue.get_queue()
    job = Q.put(job_class)

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