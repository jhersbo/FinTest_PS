from functools import wraps
from typing import Callable

from fastapi.responses import JSONResponse

from app.api.middleware.request_capture import get_request
from app.core.models.token import Token
from .responses import BadTokenException

def auth(fn):
    """
    Decorator which contains basic client permissions/authentication
    functionality which can be added to any endpoint.

    Basic usage:
    ```python
    @app.get("/")
    @auth
    async def endpoint():
        return {}

    """
    @wraps(fn)
    async def w(
        *args, 
        **kwargs
    ) ->  JSONResponse:
        # AUTHENTICATE API TOKEN
        req = get_request()
        x_api_key = req.headers.get("x-fintestps-key")
        if not x_api_key:
            raise BadTokenException()
        
        token = await Token.find_by_token(x_api_key)
        if token:
            if not token.is_valid():
                raise BadTokenException(msg="Token expired. Please obtain a new one.")
        else:
            raise BadTokenException()

        # TODO - authenticate endpoint access based on permissions group
        return await fn(*args, **kwargs)
    return w