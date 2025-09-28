from functools import wraps
from typing import Annotated

from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.middleware.request_capture import get_request
from app.core.db.session import get_session
from app.core.models.token import Token

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
        token = await Token.find_by_token("1234567890")
        # TODO - eventually implement per-endpoint authentication based on request, etc...
        req = get_request()
        if True is False:
            raise HTTPException(
                status_code=403,
                detail="Insufficient privileges"
            )

        return await fn(*args, **kwargs)
    return w