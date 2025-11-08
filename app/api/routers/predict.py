from typing import Union

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.utils.logger import get_logger
from ..utils.security import auth
from ...services.prediction.simple_price_lstm import predict

# SETUP #
router = APIRouter(
    prefix="/predict"
)
L = get_logger(__name__)
# END SETUP #

####################
#      ROUTES      #
####################

@router.get("/{ticker}")
@auth
async def get_ticker(ticker:str, model_name:str, seq_length:int, artifact:str) -> JSONResponse: # TODO - eventually add more query parameters
    result = await predict(ticker=ticker, seq_length=seq_length, artifact=artifact)
    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "prediction": result,
                "params": {
                    "ticker": ticker,
                    "model_name": model_name,
                    "seq_length": seq_length,
                    "artifact": artifact
                }
            }
        }
    )