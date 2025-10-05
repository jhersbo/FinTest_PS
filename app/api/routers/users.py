from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.utils.logger import get_logger
from app.core.models.token import Token
from ..middleware.request_capture import get_request

# SETUP
router = APIRouter(
    prefix="/users"
)
L = get_logger(__name__)
# END SETUP

####################
#      ROUTES      #
####################
@router.post("/token")
async def post_token():
    """
    Creates a token for the requesting client
    """
    req = get_request()
    token = await Token.create(req=req)

    return JSONResponse(
        {
            "result": "Ok",
            "token": token.token,
            "expiration": str(token.expiration)
        },
        status_code=status.HTTP_201_CREATED
    )


