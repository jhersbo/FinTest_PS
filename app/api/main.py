import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.routers.details import router as details_router

app = FastAPI(
    title="Prediction Service",
    version="v0.0.0.1"
)

# ROUTERS
app.include_router(details_router)
# END ROUTERS

# LOGGING
# TODO - set up sensible logging
# END LOGGING

@app.get("/")
def root():
    return JSONResponse(
        {
            "result": "Ok",
            "subject": "Hello ✌🏻"
        }
    )