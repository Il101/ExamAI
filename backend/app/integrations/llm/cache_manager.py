"""Gemini Context Cache Manager"""
from google import genai
from google.genai import types
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
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
        exam_id: Optional[UUID], 
        content: str,
        ttl_seconds: int = 3600
    ) -> str:
        """
        Create context cache for exam content
        
        Args:
            exam_id: Exam UUID or None
            content: Full exam content to cache
            ttl_seconds: Time to live in seconds (default 1 hour)
        
        Returns:
            Cache name for future reference
        """
        try:
            from app.core.config import settings
            
            # Create cache with model from settings
            cache = await self.client.aio.caches.create(
                model=settings.GEMINI_MODEL,
                config={
                    "contents": [{
                        "role": "user",
                        "parts": [{"text": content}]
                    }],
                    "ttl": f"{ttl_seconds}s",
                    "display_name": f"exam_{exam_id}" if exam_id else None
                }
            )
            
            if exam_id:
                self.caches[str(exam_id)] = {
                    "name": cache.name,
                    "created_at": datetime.now(),
                    "expires_at": datetime.now() + timedelta(seconds=ttl_seconds)
                }
            
            logger.info(f"Created cache {cache.name} for exam {exam_id}")
            return cache.name
            
        except Exception as e:
            logger.error(f"Failed to create cache for exam {exam_id}: {e}")
            raise

    async def create_cache_from_file(
        self, 
        exam_id: Optional[UUID], 
        file_uri: str,
        mime_type: str = "application/pdf",
        ttl_seconds: int = 3600
    ) -> str:
        """
        Create context cache directly from file URI (avoids extraction timeout)
        
        Args:
            exam_id: Exam UUID or None
            file_uri: URI of the file uploaded to Gemini Files API
            mime_type: MIME type of the file
            ttl_seconds: Time to live in seconds
            
        Returns:
            Cache name
        """
        try:
            from app.core.config import settings
            
            logger.info(f"[CacheManager] Creating cache from file for exam {exam_id}")
            logger.info(f"[CacheManager] File URI: {file_uri}, MIME: {mime_type}, TTL: {ttl_seconds}s")
            
            # Create cache with file data
            cache = await self.client.aio.caches.create(
                model=settings.GEMINI_MODEL,
                config={
                    "contents": [{
                        "role": "user",
                        "parts": [{"file_data": {"file_uri": file_uri, "mime_type": mime_type}}]
                    }],
                    "ttl": f"{ttl_seconds}s",
                    "display_name": f"exam_{exam_id}" if exam_id else None
                }
            )
            
            if exam_id:
                self.caches[str(exam_id)] = {
                    "name": cache.name,
                    "created_at": datetime.now(),
                    "expires_at": datetime.now() + timedelta(seconds=ttl_seconds)
                }
            
            logger.info(f"[CacheManager] ✅ Successfully created file cache: {cache.name}")
            return cache.name
            
        except Exception as e:
            logger.error(f"[CacheManager] ❌ Failed to create file cache for exam {exam_id}: {e}", exc_info=True)
            raise

    async def create_cache_from_files(
        self,
        exam_id: Optional[UUID],
        files: List[Tuple[str, str]],
        ttl_seconds: int = 3600,
    ) -> str:
        """
        Create context cache from multiple files (Gemini Files API URIs).

        Args:
            exam_id: Exam UUID or None
            files: List of tuples (file_uri, mime_type)
            ttl_seconds: Time to live in seconds

        Returns:
            Cache name
        """
        try:
            from app.core.config import settings

            if not files:
                raise ValueError("No files provided for cache creation")

            parts = [
                {"file_data": {"file_uri": uri, "mime_type": mime}}
                for uri, mime in files
            ]

            logger.info(
                f"[CacheManager] Creating cache from {len(files)} files for exam {exam_id}"
            )

            cache = await self.client.aio.caches.create(
                model=settings.GEMINI_MODEL,
                config={
                    "contents": [
                        {
                            "role": "user",
                            "parts": parts,
                        }
                    ],
                    "ttl": f"{ttl_seconds}s",
                    "display_name": f"exam_{exam_id}" if exam_id else None,
                },
            )

            if exam_id:
                self.caches[str(exam_id)] = {
                    "name": cache.name,
                    "created_at": datetime.now(),
                    "expires_at": datetime.now() + timedelta(seconds=ttl_seconds),
                }

            logger.info(f"[CacheManager] ✅ Successfully created multi-file cache: {cache.name}")
            return cache.name

        except Exception as e:
            logger.error(
                f"[CacheManager] ❌ Failed to create multi-file cache for exam {exam_id}: {e}",
                exc_info=True,
            )
            raise
    
    async def refresh_cache(self, cache_name: str, ttl_seconds: int = 3600) -> None:
        """
        Extend cache TTL
        
        Args:
            cache_name: Cache identifier
            ttl_seconds: New TTL in seconds
        """
        try:
            await self.client.aio.caches.update(
                name=cache_name,
                config=types.UpdateCachedContentConfig(ttl=f"{ttl_seconds}s")
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
            cache = await self.client.aio.caches.get(name=cache_name)
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
            await self.client.aio.caches.delete(name=cache_name)
            logger.info(f"Deleted cache {cache_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache {cache_name}: {e}")
            return False
