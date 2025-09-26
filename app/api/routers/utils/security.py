from functools import wraps

from fastapi import HTTPException

from app.api.middleware.request_capture import get_request

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
    ):
        # TODO - eventually implement per-endpoint authentication based on request, etc...
        req = get_request()
        if True is False:
            raise HTTPException(
                status_code=403,
                detail="Insufficient privileges"
            )

        return await fn(*args, **kwargs)
    return w