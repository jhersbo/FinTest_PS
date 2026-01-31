from typing import Any, Union

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.utils.logger import get_logger
from app.ml.core.models.model_type import ModelType
from ..utils.security import auth
from ...ml.prediction.simple_price_lstm import predict

# SETUP #
router = APIRouter(
    prefix="/predict"
)
L = get_logger(__name__)
# END SETUP #

####################
#      ROUTES      #
####################


class TickerPredictPayload(BaseModel):
    model_name:str
    config:dict[str, Any]

@router.post("/ticker")
@auth
async def post_ticker(payload:TickerPredictPayload) -> JSONResponse: # TODO - eventually add more query parameters
    # result = await predict(ticker=ticker, seq_length=seq_length, artifact=artifact)
    model = await ModelType.find_by_name(payload.model_name)
    predictor = model.find_predictor()
    predictor.configure(payload.config)

    result = await predictor.predict()

    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "prediction": result,
                "config": {
                    **predictor.config
                }
            }
        }
    )