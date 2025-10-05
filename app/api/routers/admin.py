"""
A series of endpoints that are used mostly for testing, but can be used
to trigger daily data processes
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.utils.logger import get_logger
from .utils.security import auth

# SETUP #
router = APIRouter(
    prefix="/admin"
)
L = get_logger(__name__)
# END SETUP #

####################
#      ROUTES      #
####################
@router.post("/savedata/daily")
@auth
async def post_saveDataDaily() -> JSONResponse:
    pass