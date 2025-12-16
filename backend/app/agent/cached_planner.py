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
    
    async def make_plan(self, state: AgentState):
        """
        Override standard make_plan to check for existing cache in state.
        This ensures even if we didn't just upload a file (e.g. retry), we use the cache.
        """
        if state.cache_name:
            logger.info(f"Using existing cache for planning: {state.cache_name}")
            # Generate plan using internal cached method
            plan = await self._make_plan_internal(state, state.cache_name)
            
            # Convert to legacy steps format to match interface
            from app.agent.plan_adapter import exam_plan_to_steps
            return exam_plan_to_steps(plan)
            
        return await super().make_plan(state)

    async def make_plan_with_cache(
        self,
        state: AgentState,
        cache_manager: ContextCacheManager,
        storage: SupabaseStorage,
        exam_id: UUID,
        file_uri: Optional[str] = None,
        mime_type: str = "application/pdf",
        file_inputs: Optional[list[dict]] = None,
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
        
        # Strategy A: Direct File Cache (Required for file uploads)
        if file_inputs:
            files_for_cache = [
                (item["uri"], item.get("mime_type", "application/pdf"))
                for item in file_inputs
                if item.get("uri")
            ]

            if not files_for_cache:
                raise ValueError("No valid file URIs provided for cache creation")

            try:
                logger.info(
                    f"Creating cache from {len(files_for_cache)} uploaded files for exam {exam_id}"
                )
                cache_name = await cache_manager.create_cache_from_files(
                    exam_id,
                    files_for_cache,
                    ttl_seconds=3600,
                )
            except Exception as e:
                logger.error("Failed to create multi-file cache", exc_info=True)
                raise

        elif file_uri:
            # Retry logic for cache creation (Gemini API can be temporarily overloaded)
            max_retries = 3
            retry_delay = 5  # Start with 5 seconds
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Creating cache from file URI: {file_uri} (attempt {attempt + 1}/{max_retries})")
                    cache_name = await cache_manager.create_cache_from_file(
                        exam_id,
                        file_uri,
                        mime_type,
                        ttl_seconds=3600
                    )
                    logger.info(f"✅ Successfully created file cache: {cache_name}")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    is_503 = "503" in error_msg or "overloaded" in error_msg or "unavailable" in error_msg
                    
                    if is_503 and attempt < max_retries - 1:
                        # Gemini API temporarily overloaded, retry with exponential backoff
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(
                            f"⚠️ Gemini API overloaded (503), retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        import asyncio
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Final attempt failed or non-503 error
                        logger.error(f"❌ Failed to create cache from file {file_uri}: {e}", exc_info=True)
                        raise ValueError(
                            f"Failed to create cache from uploaded file after {max_retries} attempts. "
                            f"The AI service is temporarily unavailable. Please try again in a few minutes."
                        ) from e
        
        # Strategy B: Text Content Cache (Only for text-only input, no file upload)
        elif state.original_content and len(state.original_content) > 4000:
            # This path is ONLY for when user pastes text directly (no file)
            token_count = len(state.original_content) // 4
            logger.info(f"Creating cache from text content ({token_count} tokens)")
            try:
                cache_name = await cache_manager.create_cache(
                    exam_id,
                    state.original_content,
                    ttl_seconds=3600
                )
                logger.info(f"✅ Created text cache for exam {exam_id}: {cache_name}")
            except Exception as e:
                logger.warning(f"Failed to create text cache: {e}. Continuing without cache.")
        else:
            logger.info(f"Content too small ({len(state.original_content)} chars) for caching, generating plan without cache")
        
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
                        import asyncio
                        response = await asyncio.wait_for(
                            self.llm.client.aio.models.generate_content(
                                model=settings.GEMINI_MODEL,  # Use base model
                                config={
                                    "cached_content": cache_name,
                                },
                                contents=[{"role": "user", "parts": [{"text": prompt}]}]
                            ),
                            timeout=120.0  # 2 minute timeout
                        )
                        
                        # Parse response
                        plan_text = response.text
                        if plan_text is None:
                            raise ValueError("Received None response from cached LLM call")
                    
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
                                    logger.info("Recreating cache from state content...")
                                    # Use exam_id from state if available
                                    cache_exam_id = UUID(state.exam_id) if state.exam_id else None
                                    new_cache_name = await cache_manager.create_cache(
                                        exam_id=cache_exam_id,
                                        content=state.original_content,
                                        ttl_seconds=3600
                                    )
                                    logger.info(f"Successfully recreated cache: {new_cache_name}")
                                    
                                    # Retry with new cache
                                    prompt = self._build_planning_prompt_with_cache(state)
                                    response = await asyncio.wait_for(
                                        self.llm.client.aio.models.generate_content(
                                            model=settings.GEMINI_MODEL,
                                            config={
                                                "cached_content": new_cache_name,
                                            },
                                            contents=[{"role": "user", "parts": [{"text": prompt}]}]
                                        ),
                                        timeout=120.0  # 2 minute timeout
                                    )
                                    plan_text = response.text
                                    if plan_text is None:
                                        raise ValueError("Received None response from recreated cache LLM call")
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
                                if plan_text is None:
                                    raise ValueError("Received None response from fallback LLM call")
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
                    if plan_text is None:
                        raise ValueError("Received None response from LLM call")
                
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
        
        # When using cache, replace content_context with VERY EXPLICIT instruction
        # The actual PDF content is already in the cache
        cache_instruction = """
---
🔴 **CRITICAL - READ THIS FIRST** 🔴

The user's study materials (PDF document, text file, or other content) have been pre-loaded into your context.
These materials are ALREADY AVAILABLE TO YOU in the conversation context above.

**YOU MUST:**
1. READ and ANALYZE the materials that are already in your context
2. EXTRACT the actual subject/topic from those materials
3. CREATE a plan based ONLY on what you find in those materials
4. DO NOT make up generic topics about programming, data science, or any other subject

**YOU MUST NOT:**
- Ignore the materials and create a generic plan
- Assume the subject based on a filename or title
- Invent topics that don't exist in the materials

**The materials are RIGHT THERE in your context. Look at them NOW before creating the plan.**
---
"""
        
        prompt = load_prompt(
            'planner/course_plan.txt',
            content_context=cache_instruction  # Replace placeholder with cache instruction
        )
        
        return prompt
