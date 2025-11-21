"""
Rate limiting middleware for tier-based API rate limiting.
"""
from fastapi import Request, Response
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.rate_limit import get_user_rate_limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies tier-based rate limiting to API requests.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # Skip rate limiting for webhooks (they have their own verification)
        if "/webhooks/" in request.url.path:
            return await call_next(request)

        # Get user from request state (set by auth dependency)
        user = getattr(request.state, "user", None)
        
        # Get rate limit for user's tier
        rate_limit_str = get_user_rate_limit(user)
        
        # Get limiter from app state
        limiter = request.app.state.limiter
        
        try:
            # Check rate limit
            # Note: slowapi's limiter.limit() is a decorator, so we use it differently
            # For middleware, we'll apply the limit directly
            await limiter._check_request_limit(
                request,
                endpoint_func=None,
                in_middleware=True
            )
        except RateLimitExceeded:
            raise
        
        response = await call_next(request)
        return response
