"""Cache fallback service for resilient generation"""
from typing import Callable, Any, Optional
from uuid import UUID
import logging

from app.integrations.storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager

logger = logging.getLogger(__name__)


class CacheFallbackService:
    """Handles cache expiry with automatic recreation from storage"""
    
    def __init__(
        self,
        storage: SupabaseStorage,
        cache_manager: ContextCacheManager
    ):
        self.storage = storage
        self.cache = cache_manager
    
    async def execute_with_fallback(
        self,
        exam_id: UUID,
        cache_name: Optional[str],
        operation: Callable[[Optional[str]], Any]
    ) -> Any:
        """
        Execute operation with automatic cache recreation on expiry
        
        Args:
            exam_id: Exam UUID
            cache_name: Current cache name (may be expired)
            operation: Async function that takes cache_name and returns result
        
        Returns:
            Operation result
        
        Raises:
            Original exception if not cache-related
        """
        try:
            return await operation(cache_name)
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if cache expired
            if "cache" in error_str and ("not found" in error_str or "expired" in error_str):
                logger.warning(f"Cache expired for exam {exam_id}, recreating...")
                
                # 1. Download file from storage
                file_path = f"exams/{exam_id}/original_content.txt"
                try:
                    content_bytes = await self.storage.download_file(file_path)
                    content = content_bytes.decode('utf-8')
                    logger.info(f"Downloaded content from storage: {file_path}")
                except Exception as download_error:
                    logger.error(f"Failed to download from storage: {download_error}")
                    raise ValueError(f"Cache expired and content not found in storage") from download_error
                
                # 2. Recreate cache
                try:
                    new_cache_name = await self.cache.create_cache(
                        exam_id,
                        content,
                        ttl_seconds=3600
                    )
                    logger.info(f"Recreated cache: {new_cache_name}")
                except Exception as cache_error:
                    logger.error(f"Failed to recreate cache: {cache_error}")
                    raise ValueError(f"Failed to recreate cache") from cache_error
                
                # 3. Retry operation with new cache
                try:
                    return await operation(new_cache_name)
                except Exception as retry_error:
                    logger.error(f"Operation failed even after cache recreation: {retry_error}")
                    raise
            else:
                # Not a cache error, re-raise
                raise
    
    async def generate_with_cache(
        self,
        exam_id: UUID,
        cache_name: Optional[str],
        prompt: str,
        llm_client: Any,
        fallback_content: Optional[str] = None
    ) -> str:
        """
        Centralized method to generate content with automatic cache fallback
        
        Args:
            exam_id: Exam UUID
            cache_name: Cache identifier (may be None or expired)
            prompt: Prompt to send
            llm_client: LLM client instance (e.g., self.llm.client)
            fallback_content: Optional content to use if cache fails and storage unavailable
        
        Returns:
            Generated text
        
        Example:
            result = await fallback_service.generate_with_cache(
                exam_id=exam.id,
                cache_name=exam.cache_name,
                prompt="Generate plan...",
                llm_client=self.llm.client,
                fallback_content=exam.original_content
            )
        """
        async def operation(cache: Optional[str]):
            if cache:
                # Use cache
                response = await llm_client.aio.models.generate_content(
                    model=cache,
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )
                return response.text
            else:
                # No cache - need content
                if not fallback_content:
                    raise ValueError("No cache and no fallback content provided")
                
                # Use fallback content directly
                # This requires the caller to handle generation without cache
                raise ValueError("Cache not available, use fallback_content")
        
        try:
            return await self.execute_with_fallback(exam_id, cache_name, operation)
        except ValueError as e:
            if "use fallback_content" in str(e) and fallback_content:
                # Caller should handle this case
                raise
            raise
