import time
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi.responses import JSONResponse
from redis import Redis

from app.core.config.config import get_config
from app.core.utils.logger import get_logger

L = get_logger(__name__)

class RateLimiter(BaseHTTPMiddleware):
    """
    Redis-backed sliding window rate limiter middleware.

    Tracks requests per client IP and enforces configurable rate limits.
    Uses Redis for distributed rate limiting across multiple workers/instances.
    """

    # Rate limit configuration
    MAX_REQUESTS = 100  # Maximum requests per window
    WINDOW_SECONDS = 60  # Time window in seconds (1 minute)

    # Whitelist paths that bypass rate limiting
    EXEMPT_PATHS = []

    def __init__(self, app, max_requests: int = None, window_seconds: int = None): #TODO - this is creating a new object on every request
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application instance
            max_requests: Override default max requests per window
            window_seconds: Override default window size in seconds
        """
        super().__init__(app)

        if max_requests is not None:
            self.MAX_REQUESTS = max_requests
        if window_seconds is not None:
            self.WINDOW_SECONDS = window_seconds

        # Initialize Redis connection
        try:
            config = get_config()
            self.redis:Redis = Redis(
                host="redis",  # Using service name from RedisQueue
                port=int(config.redis_port),
                db=1,  # Use db=1 for rate limiting (db=0 is for RQ)
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis.ping()
            self.enabled = True
            L.info(f"Rate limiter initialized: {self.MAX_REQUESTS} requests per {self.WINDOW_SECONDS}s window")
        except Exception as e:
            L.warning(f"Rate limiter disabled - Redis connection failed: {e}")
            self.enabled = False

    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce rate limiting.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response or 429 error if rate limited
        """
        # Skip rate limiting if disabled or path is exempt
        if not self.enabled or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)

        # Check rate limit
        allowed, current_count, reset_time = self._check_rate_limit(client_ip)

        if not allowed:
            L.warning(f"Rate limit exceeded for {client_ip}: {current_count}/{self.MAX_REQUESTS} requests")
            return JSONResponse(
                status_code=429,
                content={
                    "result": "Error",
                    "detail": "Too many requests. Please try again later.",
                    "rate_limit": {
                        "limit": self.MAX_REQUESTS,
                        "window_seconds": self.WINDOW_SECONDS,
                        "current": current_count,
                        "reset_at": reset_time
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(self.MAX_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(max(1, reset_time - int(time.time())))
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = max(0, self.MAX_REQUESTS - current_count)
        response.headers["X-RateLimit-Limit"] = str(self.MAX_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Checks X-Forwarded-For header first (for proxied requests),
        falls back to direct client address.

        Args:
            request: HTTP request

        Returns:
            Client IP address as string
        """
        # Check for proxied requests
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP (used by some proxies)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct client
        if request.client:
            return request.client.host

        return "unknown"

    def _check_rate_limit(self, client_ip: str) -> tuple[bool, int, int]:
        """
        Check if client has exceeded rate limit using sliding window algorithm.

        Uses Redis sorted set to track request timestamps within the time window.

        Args:
            client_ip: Client identifier (IP address)

        Returns:
            Tuple of (allowed, current_count, reset_time)
            - allowed: True if request is allowed, False if rate limited
            - current_count: Number of requests in current window
            - reset_time: Unix timestamp when the window resets
        """
        try:
            current_time = time.time()
            window_start = current_time - self.WINDOW_SECONDS
            redis_key = f"rate_limit:{client_ip}"

            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Remove requests older than the window
            pipe.zremrangebyscore(redis_key, 0, window_start)

            # Count requests in current window
            pipe.zcard(redis_key)

            # Add current request timestamp
            pipe.zadd(redis_key, {str(current_time): current_time})

            # Set expiration on the key (cleanup)
            pipe.expire(redis_key, self.WINDOW_SECONDS + 1)

            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]  # Count from zcard

            # Calculate reset time (end of current window)
            reset_time = int(current_time + self.WINDOW_SECONDS)

            # Check if limit exceeded (count before adding current request)
            allowed = current_count < self.MAX_REQUESTS

            return allowed, current_count + 1, reset_time

        except Exception as e:
            L.error(f"Rate limit check failed for {client_ip}: {e}")
            # On error, allow the request (fail open)
            return True, 0, int(time.time() + self.WINDOW_SECONDS)

    def reset_client(self, client_ip: str) -> bool:
        """
        Reset rate limit for a specific client (admin function).

        Args:
            client_ip: Client IP to reset

        Returns:
            True if successful, False otherwise
        """
        try:
            redis_key = f"rate_limit:{client_ip}"
            self.redis.delete(redis_key)
            L.info(f"Rate limit reset for {client_ip}")
            return True
        except Exception as e:
            L.error(f"Failed to reset rate limit for {client_ip}: {e}")
            return False

    def get_client_stats(self, client_ip: str) -> Optional[dict]:
        """
        Get current rate limit statistics for a client.

        Args:
            client_ip: Client IP address

        Returns:
            Dict with current count and remaining requests, or None on error
        """
        try:
            current_time = time.time()
            window_start = current_time - self.WINDOW_SECONDS
            redis_key = f"rate_limit:{client_ip}"

            # Count requests in current window
            count = self.redis.zcount(redis_key, window_start, current_time)
            remaining = max(0, self.MAX_REQUESTS - count)

            return {
                "client_ip": client_ip,
                "current_count": count,
                "limit": self.MAX_REQUESTS,
                "remaining": remaining,
                "window_seconds": self.WINDOW_SECONDS
            }
        except Exception as e:
            L.error(f"Failed to get stats for {client_ip}: {e}")
            return None