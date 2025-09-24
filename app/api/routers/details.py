from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.clients.polygon_client import PolygonClient

router = APIRouter(
    prefix="/details"
)

# CLIENTS
P = PolygonClient()
# END CLIENTS

@router.get("/dms")
async def get_DMS() -> JSONResponse:
    try:
        result = await P.getDMS()
        return JSONResponse(
            {
                "result": "Ok",
                "subject": {
                    "data": result.to_json(orient="records")
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            content=e,
            status_code=500
        )