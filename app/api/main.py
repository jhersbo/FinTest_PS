from fastapi import FastAPI, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routers.details import router as details_router
from app.api.routers.users import router as users_router
from app.core.utils.logger import get_logger
from app.api.routers.utils.responses import WrappedException
from app.api.middleware.request_capture import RequestCapture
from app.api.middleware.rate_limiter import RateLimiter

from ..services.clients.av_client import AVClient

L = get_logger(__name__)

app = FastAPI(
    title="Prediction Service",
    version="v0.0.0.1"
)

# ROUTERS
app.include_router(users_router)
app.include_router(details_router)
# END ROUTERS

# MIDDLEWARE
app.add_middleware(RequestCapture)
app.add_middleware(RateLimiter)
# END MIDDLEWARE

@app.exception_handler(WrappedException)
async def wrapped_exception_handler(request: Request, exc: WrappedException) -> JSONResponse:
    L.exception(exc)
    return JSONResponse(
        {
            "result": "Error",
            "subject": exc.msg
        },
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request:Request, exc: Exception) -> JSONResponse:
    L.exception(exc)
    return JSONResponse(
        {
            "result": "Error",
            "subject": "An exception occured"
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

@app.get("/")
def root():
    return JSONResponse(
        {
            "result": "Ok",
            "subject": "Hello ✌🏻"
        }
    )

@app.get("/test")
async def test():
    A = AVClient()
    res = await A.time_series_daily(symbol="AAPL", adjusted=False, full=False)

    return JSONResponse(
        {
            "result": "Ok",
            "subject": res.to_dict(orient="records")
        }
    )
