from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ...api.routers.utils.responses import WrappedException

class RateLimiter(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if False:
            return JSONResponse(
                status_code=429,
                content={
                    "result": "Error",
                    "detail": "Too many requests"
                }
            )
        
        return await call_next(request)