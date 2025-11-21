"""
Rate limiting utilities for tier-based API rate limiting.
"""
from functools import wraps
from typing import Callable

from fastapi import Request
from slowapi import Limiter

from app.domain.user import User


def get_user_rate_limit(user: User | None) -> str:
    """
    Get rate limit string based on user's subscription tier.
    
    Returns:
        - "100/hour" for free tier or unauthenticated
        - "1000/hour" for pro tier
        - "10000/hour" for premium tier (effectively unlimited)
    """
    if not user:
        return "100/hour"
    
    tier = getattr(user, "subscription_tier", "free")
    
    rate_limits = {
        "free": "100/hour",
        "pro": "1000/hour",
        "premium": "10000/hour",  # Effectively unlimited
    }
    
    return rate_limits.get(tier, "100/hour")


def dynamic_rate_limit(request: Request) -> str:
    """
    Dynamic rate limit function that returns limit based on user tier.
    Used with @limiter.limit(dynamic_rate_limit).
    """
    user = getattr(request.state, "user", None)
    return get_user_rate_limit(user)
