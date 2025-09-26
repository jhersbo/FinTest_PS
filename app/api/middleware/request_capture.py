from typing import Union

from contextvars import ContextVar
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context var to hold current request
R: ContextVar[Request] = ContextVar("request")

class RequestCapture(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = R.set(request)
        try:
            response = await call_next(request)
        finally:
            R.reset(token)
        return response
    
def get_request() -> Union[Request, None]:
    """Access the current request object."""
    return R.get(None)