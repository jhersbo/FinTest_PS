from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routers.details import router as details_router
from app.api.routers.users import router as users_router
from app.api.routers.admin import router as admin_router
from .routers.train import router as train_router
from .routers.predict import router as predict_router
from .routers.rate_limit import router as rl_router
from app.core.utils.logger import get_logger
from app.api.utils.responses import WrappedException
from app.api.middleware.request_capture import RequestCapture
from app.api.middleware.rate_limiter import RateLimiter

L = get_logger(__name__)

app = FastAPI(
    title="FinTest Prediction Service",
    version="v0.0.0.2"
)

routers = [
    users_router,
    details_router,
    train_router,
    predict_router,
    rl_router,
    admin_router
]

# ROUTERS
for r in routers:
    app.include_router(r)
# END ROUTERS

# MIDDLEWARE
middleware = [
    RequestCapture,
    RateLimiter
]
for m in middleware:
    app.add_middleware(m)
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
