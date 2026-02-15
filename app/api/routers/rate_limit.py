from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.core.utils.logger import get_logger

L = get_logger(__name__)

router = APIRouter(
    prefix="/rate-limit",
    tags=["Rate Limiting"]
)

@router.get("/status")
async def get_rate_limit_status(request: Request):
    """
    Get current rate limit status for the requesting client.

    Returns information about:
    - Current request count
    - Remaining requests in window
    - Rate limit configuration
    """
    # Access rate limiter from app middleware
    rate_limiter = None
    for middleware in request.app.user_middleware:
        if middleware.cls.__name__ == "RateLimiter":
            rate_limiter = middleware.cls
            break

    if not rate_limiter or not hasattr(rate_limiter, 'get_client_stats'):
        return JSONResponse(
            status_code=503,
            content={
                "result": "Error",
                "detail": "Rate limiter not available"
            }
        )

    # Get client IP
    client_ip = _get_client_ip(request)

    # Get stats
    stats = rate_limiter(request.app).get_client_stats(client_ip)

    if stats is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve rate limit stats")

    return JSONResponse(
        content={
            "result": "Ok",
            "data": stats
        }
    )

@router.post("/reset/{client_ip}")
async def reset_rate_limit(client_ip: str, request: Request):
    """
    Reset rate limit for a specific client IP (admin only).

    Args:
        client_ip: IP address to reset
    """
    # TODO: Add authentication check here
    # For now, this is accessible to anyone - should be protected in production

    # Access rate limiter from app middleware
    rate_limiter = None
    for middleware in request.app.user_middleware:
        if middleware.cls.__name__ == "RateLimiter":
            rate_limiter = middleware.cls
            break

    if not rate_limiter or not hasattr(rate_limiter, 'reset_client'):
        return JSONResponse(
            status_code=503,
            content={
                "result": "Error",
                "detail": "Rate limiter not available"
            }
        )

    # Reset the client
    success = rate_limiter(request.app).reset_client(client_ip)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset rate limit")

    return JSONResponse(
        content={
            "result": "Ok",
            "detail": f"Rate limit reset for {client_ip}"
        }
    )

def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"
