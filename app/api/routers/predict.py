from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.utils.logger import get_logger
from app.ml.core.models.model_type import ModelType
from app.ml.core.models.training_run import TrainingRun
from app.ml.model_defs.model_facade import ModelFacade
from ..utils.security import auth

# SETUP #
router = APIRouter(
    prefix="/predict"
)
L = get_logger(__name__)
# END SETUP #

####################
#      ROUTES      #
####################


class TrainingRunPredictPayload(BaseModel):
    gid_training_run:int
    artifact:str
    seq_len:int

@router.post("/training_run")
@auth
async def post_ticker(payload:TrainingRunPredictPayload) -> JSONResponse:
    training_run = await TrainingRun.find_by_id(payload.gid_training_run)

    if not training_run:
        return JSONResponse(
            {"result": "Error", "detail": f"TrainingRun {payload.gid_training_run} not found"},
            status_code=status.HTTP_404_NOT_FOUND
        )

    model = await ModelType.find_by_gid(training_run.gid_model_type)
    predictor = ModelFacade.predictor_for(model)
    predictor.training_run = training_run
    config = ModelFacade.build_config(
        training_run.gid, 
        {
            "artifact":payload.artifact,
            "seq_len":payload.seq_len
        },
        training_run.data
    )
    print(config)
    predictor.configure(config)

    result = await predictor.predict()

    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "prediction": result,
                "gid_training_run": training_run.gid,
                "config": {
                    **predictor.config
                }
            }
        }
    )