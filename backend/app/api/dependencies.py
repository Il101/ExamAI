"""Dependency injection for v3.0 services"""
from functools import lru_cache
from redis import Redis
from google import genai
from google.genai import types

from app.core.config import settings
from app.integrations.storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager
from app.integrations.llm.gemini import GeminiProvider
# Import get_llm_provider from the main dependencies file to avoid duplication
from app.dependencies import get_llm_provider


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
    from google.genai import types
    
    llm_provider = get_llm_provider()
    # Ensure it's the expected provider type
    if not isinstance(llm_provider, GeminiProvider):
         # This might happen if config changed to OpenAI etc.
         # For now, explicit creation or assume it is GeminiProvider
         pass 

    return ContextCacheManager(llm_provider)


def get_cache_fallback_service() -> "CacheFallbackService":
    """Get Cache Fallback Service instance"""
    from app.services.cache_fallback import CacheFallbackService
    
    storage = get_storage()
    cache_manager = get_cache_manager()
    
    return CacheFallbackService(storage, cache_manager)

