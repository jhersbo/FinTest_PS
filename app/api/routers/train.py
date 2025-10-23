from typing import Union

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.utils.logger import get_logger
from ..utils.security import auth
from ..utils.responses import WrappedException
from ...services.training.simple_price_lstm import SimplePriceLSTM

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
async def post_(payload:TickerTrainPayload) -> JSONResponse: #TODO this can eventually become a means to trigger a job    
    await SimplePriceLSTM.train(payload.ticker, num_epochs=payload.epochs)

    return JSONResponse(
        {
            "result": "Ok"
        },
        status_code=status.HTTP_201_CREATED
    )