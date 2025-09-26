from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.routers.details import router as details_router
from app.utils.logger import get_logger
from app.api.middleware.request_capture import RequestCapture

L = get_logger(__name__)

app = FastAPI(
    title="Prediction Service",
    version="v0.0.0.1"
)

# ROUTERS
app.include_router(details_router)
# END ROUTERS

# MIDDLEWARE
app.add_middleware(RequestCapture)
# END MIDDLEWARE

# TODO - eventually refactor this to handle specific exceptions
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    L.exception(exc)
    return JSONResponse(
        {
            "result": "Error"
        },
        status_code=500
    )

@app.get("/")
def root():
    return JSONResponse(
        {
            "result": "Ok",
            "subject": "Hello ✌🏻"
        }
    )
