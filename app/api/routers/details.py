import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.clients.polygon_client import PolygonClient
from app.utils.logger import get_logger

# CLIENTS
P = PolygonClient()
# END CLIENTS

# SETUP #
router = APIRouter(
    prefix="/details"
)
L = get_logger(__name__)
# END SETUP #

####################
#      ROUTES      #
####################
@router.get("/dms")
async def get_DMS() -> JSONResponse:
    try:
        result = await P.getDMS()
        return JSONResponse(
            {
                "result": "Ok",
                "subject": {
                    "data": result.to_dict(orient="records")
                }
            }
        )
    except Exception as e:
        L.exception(e)
        return JSONResponse(
            content={"result": "Error"}
        )

@router.get("/{ticker}")
async def get_Details(ticker):
    try:
        if ticker is None:
            raise Exception("Ticker arg is missing.")
        result = await P.getDetails(ticker=ticker)
        return JSONResponse(
            {
                "result": "Ok",
                "subject": {
                    "data": json.loads(result.to_json(orient="records"))
                }
            }
        )
    except Exception as e:
        L.exception(e)
        return JSONResponse(
            content={"result": "Error"}
        )