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


class UsageTracker:
    """
    Redis-based usage tracker for daily limits.
    """
    def __init__(self, key_prefix: str, seconds: int = 86400):
        self.key_prefix = key_prefix
        self.seconds = seconds
        self.redis: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        if self.redis is None:
            self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        return self.redis

    async def get_count(self, identifier: str) -> int:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"usage:{self.key_prefix}:{identifier}:{today}"
        r = await self.get_redis()
        count = await r.get(key)
        return int(count) if count else 0

    async def increment(self, identifier: str) -> int:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"usage:{self.key_prefix}:{identifier}:{today}"
        r = await self.get_redis()
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, self.seconds)
        return count


class SessionTracker:
    """
    Redis-based session tracker for enforcing simultaneous session limits.
    """
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def get_redis(self) -> redis.Redis:
        if self.redis is None:
            self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        return self.redis

    async def add_session(self, user_id: str, session_id: str, limit: int, ttl: int = 3600):
        """Add new session and enforce limit by removing oldest if necessary."""
        import time
        r = await self.get_redis()
        key_pattern = f"session:{user_id}:*"
        session_key = f"session:{user_id}:{session_id}"
        now = time.time()

        # Get all existing sessions for this user
        existing_keys = await r.keys(key_pattern)
        
        if len(existing_keys) >= limit:
            # Get values (timestamps) for all keys to find the oldest
            session_data = []
            for k in existing_keys:
                ts = await r.get(k)
                try:
                    session_data.append((k, float(ts)))
                except (ValueError, TypeError):
                    # If value is not a timestamp (legacy or corrupted), treat as very old
                    session_data.append((k, 0.0))
            
            # Sort by timestamp (asc)
            session_data.sort(key=lambda x: x[1])
            
            # Delete oldest sessions until we are under the limit
            to_delete = len(session_data) - limit + 1
            for i in range(to_delete):
                await r.delete(session_data[i][0])

        await r.setex(session_key, ttl, str(now))

    async def is_session_active(self, user_id: str, session_id: str) -> bool:
        """Check if a specific session is still active."""
        r = await self.get_redis()
        session_key = f"session:{user_id}:{session_id}"
        return await r.exists(session_key) > 0

    async def remove_session(self, user_id: str, session_id: str):
        """Remove a session."""
        r = await self.get_redis()
        session_key = f"session:{user_id}:{session_id}"
        await r.delete(session_key)

# Global trackers
tutor_usage_tracker = UsageTracker("tutor_messages")
exam_creation_tracker = UsageTracker("exam_creations")
session_tracker = SessionTracker()
