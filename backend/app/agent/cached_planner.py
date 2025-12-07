"""Extended planner with cache integration"""
from typing import Tuple, Optional
from uuid import UUID

from app.agent.planner import CoursePlanner
from app.agent.state import AgentState
from app.agent.schemas import ExamPlan
from app.integrations.storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager
import logging

logger = logging.getLogger(__name__)


class CachedCoursePlanner(CoursePlanner):
    """Planner with integrated cache creation"""
    
    async def make_plan_with_cache(
        self,
        state: AgentState,
        cache_manager: ContextCacheManager,
        storage: SupabaseStorage,
        exam_id: UUID,
        file_uri: Optional[str] = None,
        mime_type: str = "application/pdf"
    ) -> Tuple[ExamPlan, Optional[str]]:
        """
        Generate plan and create cache simultaneously
        
        Args:
            state: AgentState with content
            cache_manager: Cache manager instance
            storage: Storage service
            exam_id: Exam UUID
            file_uri: Optional URI of file uploaded to Gemini for direct caching
            mime_type: MIME type of the file
        
        Returns:
            Tuple of (ExamPlan, cache_name or None)
        """
        # 1. Upload file to storage (archival)
        if state.original_content:
            file_path = f"exams/{exam_id}/original_content.txt"
            try:
                await storage.upload_file(
                    state.original_content.encode('utf-8'),
                    file_path
                )
                logger.info(f"Uploaded content to storage: {file_path}")
            except Exception as e:
                logger.error(f"Failed to upload to storage: {e}")
                # Continue anyway
        
        # 2. Create cache
        cache_name = None
        
        # Strategy A: Direct File Cache (Best for PDFs/Docs)
        if file_uri:
            try:
                logger.info(f"Creating cache from file URI: {file_uri}")
                cache_name = await cache_manager.create_cache_from_file(
                    exam_id,
                    file_uri,
                    mime_type,
                    ttl_seconds=3600
                )
                logger.info(f"✅ Successfully created cache from file: {cache_name}")
            except Exception as e:
                logger.error(f"❌ Failed to create cache from file {file_uri}: {e}", exc_info=True)
                # Don't silently fall back - log the issue prominently
                logger.warning(f"⚠️  Cache creation failed! Will attempt fallback to text content if available.")
        
        # Strategy B: Text Content Cache (Fallback or for Text input)
        # Only if cache wasn't created by Strategy A
        if not cache_name and state.original_content:
            token_count = len(state.original_content) // 4
            
            if token_count > 1000:
                try:
                    cache_name = await cache_manager.create_cache(
                        exam_id,
                        state.original_content,
                        ttl_seconds=3600  # 1 hour
                    )
                    logger.info(f"Created cache for exam {exam_id}: {cache_name}")
                except Exception as e:
                    logger.warning(f"Failed to create cache: {e}. Continuing without cache.")
            else:
                logger.info(f"Content too small ({token_count} tokens) and no file URI, skipping cache")
        
        # 3. Generate plan (call internal method that returns ExamPlan, not adapter version)
        plan = await self._make_plan_internal(state, cache_name)
        
        return plan, cache_name
    
    async def _make_plan_internal(self, state: AgentState, cache_name: str = None) -> ExamPlan:
        """Internal method that returns ExamPlan before adapter conversion"""
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # If we have a cache, use it instead of including full content
                if cache_name:
                    try:
                        # Use cache - minimal prompt without content
                        prompt = self._build_planning_prompt_with_cache(state)
                        
                        # Call with cache
                        from app.core.config import settings
                        response = await self.llm.client.aio.models.generate_content(
                            model=settings.GEMINI_MODEL,  # Use base model
                            config={
                                "cached_content": cache_name,
                            },
                            contents=[{"role": "user", "parts": [{"text": prompt}]}]
                        )
                        
                        # Parse response
                        plan_text = response.text
                    
                    except Exception as cache_error:
                        # Check if cache expired
                        error_str = str(cache_error).lower()
                        if "cache" in error_str and ("not found" in error_str or "expired" in error_str or "404" in error_str):
                            logger.warning(f"Cache expired during plan generation, attempting to recreate...")
                            
                            # Try to recreate cache from storage
                            try:
                                # Import here to avoid circular dependency
                                from app.integrations.storage.supabase_storage import SupabaseStorage
                                from app.integrations.llm.cache_manager import ContextCacheManager
                                from app.core.config import settings
                                
                                # Initialize services
                                storage = SupabaseStorage(
                                    url=settings.SUPABASE_URL,
                                    key=settings.SUPABASE_KEY,
                                    bucket=settings.SUPABASE_BUCKET
                                )
                                cache_manager = ContextCacheManager(self.llm)
                                
                                # Download content from storage
                                # We need exam_id - it should be in state or passed separately
                                # For now, try to get from state.original_content
                                if state.original_content:
                                    # Recreate cache
                                    # Note: We don't have exam_id here, so we'll use a temporary approach
                                    # Better solution: pass exam_id to this method
                                    logger.info("Recreating cache from state content...")
                                    new_cache_name = await cache_manager.create_cache(
                                        exam_id=None,  # TODO: Pass exam_id properly
                                        content=state.original_content,
                                        ttl_seconds=3600
                                    )
                                    logger.info(f"Successfully recreated cache: {new_cache_name}")
                                    
                                    # Retry with new cache
                                    prompt = self._build_planning_prompt_with_cache(state)
                                    response = await self.llm.client.aio.models.generate_content(
                                        model=settings.GEMINI_MODEL,
                                        config={
                                            "cached_content": new_cache_name,
                                        },
                                        contents=[{"role": "user", "parts": [{"text": prompt}]}]
                                    )
                                    plan_text = response.text
                                else:
                                    raise ValueError("No content available to recreate cache")
                                    
                            except Exception as recreate_error:
                                logger.error(f"Failed to recreate cache: {recreate_error}")
                                # Final fallback: use full content
                                logger.warning("Falling back to full content generation")
                                prompt = self._build_planning_prompt(state)
                                
                                response = await self.llm.generate(
                                    prompt=prompt,
                                    temperature=0.3,
                                    max_tokens=16000,
                                    response_mime_type="application/json",
                                    response_schema=ExamPlan,
                                )
                                
                                plan_text = response.content
                        else:
                            # Not a cache error, re-raise
                            raise
                else:
                    # No cache - use full prompt with content
                    prompt = self._build_planning_prompt(state)
                    
                    response = await self.llm.generate(
                        prompt=prompt,
                        temperature=0.3,
                        max_tokens=16000,
                        response_mime_type="application/json",
                        response_schema=ExamPlan,
                    )
                    
                    plan_text = response.content
                
                # Parse and validate (returns ExamPlan, not converted)
                plan = self._parse_plan_response(plan_text)
                self._validate_plan(plan)
                
                return plan
                
            except Exception as e:
                last_error = e
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate plan after {max_retries} attempts: {str(e)}")
        
        raise ValueError(f"Plan generation failed: {str(last_error)}")
    
    def _build_planning_prompt_with_cache(self, state: AgentState) -> str:
        """Build minimal prompt when using cache (content already in cache)"""
        from app.prompts import load_prompt
        
        # When using cache, DON'T include content_context placeholder
        # The actual PDF content is already in the cache
        # Including a placeholder causes AI to ignore the cached content
        prompt = load_prompt(
            'planner/course_plan.txt'
        )
        
        # Remove the content_context section from prompt
        # since it's already in cache
        import re
        # Remove the "## Study Materials" section entirely
        prompt = re.sub(
            r'## Study Materials\s+\{content_context\}\s+---',
            '**IMPORTANT:** The study materials have already been loaded into the context. Analyze them to create the plan.\n\n---',
            prompt,
            flags=re.DOTALL
        )
        
        return prompt
