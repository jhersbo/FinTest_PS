from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routers.details import router as details_router
from app.api.routers.client_auth import router as client_router
from app.utils.logger import get_logger
from app.api.routers.utils.responses import WrappedException
from app.api.middleware.request_capture import RequestCapture
from app.api.middleware.rate_limiter import RateLimiter

L = get_logger(__name__)

app = FastAPI(
    title="Prediction Service",
    version="v0.0.0.1"
)

# ROUTERS
app.include_router(client_router)
app.include_router(details_router)
# END ROUTERS

# MIDDLEWARE
app.add_middleware(RequestCapture)
app.add_middleware(RateLimiter)
# END MIDDLEWARE

# TODO - eventually refactor this to handle specific exceptions
@app.exception_handler(WrappedException)
async def wrapped_exception_handler(request: Request, exc: WrappedException) -> JSONResponse:
    L.exception(exc)
    raise HTTPException(
        detail=exc.msg,
        status_code=exc.status_code
    )

@app.get("/")
def root():
    return JSONResponse(
        {
            "result": "Ok",
            "subject": "Hello ✌🏻"
        }
    )
