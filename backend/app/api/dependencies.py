"""Dependency injection for v3.0 services"""
from functools import lru_cache
from redis import Redis
from google import genai

from app.core.config import settings
from app.integrations.storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager
from app.services.prefetch_manager import PrefetchManager


@lru_cache()
def get_redis_client() -> Redis:
    """Get Redis client instance"""
    return Redis.from_url(settings.REDIS_URL, decode_responses=False)


@lru_cache()
def get_storage() -> SupabaseStorage:
    """Get Supabase Storage instance"""
    return SupabaseStorage(
        url=settings.SUPABASE_URL,
        key=settings.SUPABASE_KEY,
        bucket=settings.SUPABASE_BUCKET
    )


@lru_cache()
def get_cache_manager() -> ContextCacheManager:
    """Get Gemini Cache Manager instance"""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return ContextCacheManager(client)


@lru_cache()
def get_prefetch_manager() -> PrefetchManager:
    """Get Prefetch Manager instance"""
    redis = get_redis_client()
    return PrefetchManager(redis)
