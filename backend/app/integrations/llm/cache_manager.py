"""Gemini Context Cache Manager"""
from google import genai
from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ContextCacheManager:
    """Manages Gemini context caching for exam content"""
    
    def __init__(self, client: genai.Client):
        self.client = client
        self.caches: Dict[str, any] = {}  # Cache metadata storage
    
    async def create_cache(
        self, 
        exam_id: UUID, 
        content: str,
        ttl_seconds: int = 3600
    ) -> str:
        """
        Create context cache for exam content
        
        Args:
            exam_id: Exam UUID
            content: Full exam content to cache
            ttl_seconds: Time to live in seconds (default 1 hour)
        
        Returns:
            Cache name for future reference
        """
        try:
            # Create cache with model as direct parameter
            cache = await self.client.aio.caches.create(
                model="gemini-2.5-flash-lite",
                config={
                    "contents": [{
                        "role": "user",
                        "parts": [{"text": content}]
                    }],
                    "ttl": f"{ttl_seconds}s",
                    "display_name": f"exam_{exam_id}"
                }
            )
            
            self.caches[str(exam_id)] = {
                "name": cache.name,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(seconds=ttl_seconds)
            }
            
            logger.info(f"Created cache for exam {exam_id}: {cache.name}")
            return cache.name
            
        except Exception as e:
            logger.error(f"Failed to create cache for exam {exam_id}: {e}")
            raise
    
    async def refresh_cache(self, cache_name: str, ttl_seconds: int = 3600) -> None:
        """
        Extend cache TTL
        
        Args:
            cache_name: Cache identifier
            ttl_seconds: New TTL in seconds
        """
        try:
            await self.client.caches.update(
                name=cache_name,
                ttl=f"{ttl_seconds}s"
            )
            logger.info(f"Refreshed cache {cache_name} with TTL {ttl_seconds}s")
        except Exception as e:
            logger.error(f"Failed to refresh cache {cache_name}: {e}")
            raise
    
    async def get_cache_info(self, cache_name: str) -> Optional[Dict]:
        """
        Get cache metadata
        
        Args:
            cache_name: Cache identifier
        
        Returns:
            Dict with cache info or None if not found
        """
        try:
            cache = await self.client.caches.get(name=cache_name)
            ttl_remaining = (cache.expire_time - datetime.now()).total_seconds()
            
            return {
                "name": cache.name,
                "expire_time": cache.expire_time,
                "ttl_remaining": ttl_remaining,
                "should_refresh": ttl_remaining < 300  # Refresh if <5 min remaining
            }
        except Exception as e:
            logger.warning(f"Failed to get cache info for {cache_name}: {e}")
            return None
    
    async def delete_cache(self, cache_name: str) -> bool:
        """
        Delete cache
        
        Args:
            cache_name: Cache identifier
        
        Returns:
            True if deleted successfully
        """
        try:
            await self.client.caches.delete(name=cache_name)
            logger.info(f"Deleted cache {cache_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache {cache_name}: {e}")
            return False
