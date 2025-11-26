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


def get_generation_service() -> "GenerationService":
    """Get Generation Service instance"""
    from app.services.generation_service import GenerationService
    from app.agent.cached_executor import CachedTopicExecutor
    from app.integrations.llm.gemini import GeminiProvider
    from app.core.config import settings
    
    llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    executor = CachedTopicExecutor(llm)
    prefetch = get_prefetch_manager()
    fallback = get_cache_fallback_service()
    
    return GenerationService(executor, prefetch, fallback)


def get_cache_fallback_service() -> "CacheFallbackService":
    """Get Cache Fallback Service instance"""
    from app.services.cache_fallback import CacheFallbackService
    
    storage = get_storage()
    cache_manager = get_cache_manager()
    
    return CacheFallbackService(storage, cache_manager)
