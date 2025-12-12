from typing import Optional
import time

from fastapi import HTTPException, Request, status
import redis.asyncio as redis

from app.core.config import settings


class RateLimiter:
    """
    Simple Redis-based Rate Limiter.
    """
    def __init__(self, times: int = 5, seconds: int = 60):
        self.times = times
        self.seconds = seconds
        self.redis: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        if self.redis is None:
            self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        return self.redis

    async def __call__(self, request: Request):
        if settings.ENVIRONMENT == "test":
            return

        try:
            client_ip = request.client.host if request.client else "127.0.0.1"
            endpoint = request.url.path
            key = f"rate_limit:{endpoint}:{client_ip}"
            
            r = await self.get_redis()
            
            # Simple fixed window counter
            # Increment request count
            current = await r.incr(key)
            
            # Set expiry on new key
            if current == 1:
                await r.expire(key, self.seconds)
                
            if current > self.times:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Please try again in {self.seconds} seconds."
                )
        except HTTPException:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            # Fail open - if Redis is unavailable, allow the request
            # Log error for monitoring
            import logging
            logging.getLogger(__name__).warning(f"Rate limiter error (failing open): {e}")

# Dependency instances
login_rate_limiter = RateLimiter(times=5, seconds=60) # 5 attempts per minute
general_rate_limiter = RateLimiter(times=60, seconds=60) # 60 attempts per minute
