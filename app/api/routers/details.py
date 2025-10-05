import json
from typing import Annotated

from fastapi import APIRouter, HTTPException, Header, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.clients.polygon_client import PolygonClient
from app.core.utils.logger import get_logger
from .utils.security import auth
from app.core.db.session import inject_db

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
@auth
async def get_DMS() -> JSONResponse:
    result = await P.getDMS()
    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "data": result.to_dict(orient="records")
            }
        }
    )

@router.get("/{ticker}")
@auth
async def get_Details(ticker:str) -> JSONResponse:
    result = await P.getDetails(ticker=ticker)
    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "data": json.loads(result.to_json(orient="records"))
            }
        }
    )
    
@router.get("/sma/{ticker}")
@auth
async def get_SMA(ticker:str, window:int=50, limit:int=5000) -> JSONResponse:
    result = await P.getSMA(ticker=ticker, window=window, limit=limit)
    return JSONResponse(
        {
            "result": "Ok",
            "subject": {
                "data": result.to_dict(orient="records")
            }
        }
    )