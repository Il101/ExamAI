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
        exam_id: UUID
    ) -> Tuple[ExamPlan, Optional[str]]:
        """
        Generate plan and create cache simultaneously
        
        Args:
            state: AgentState with content
            cache_manager: Cache manager instance
            storage: Storage service
            exam_id: Exam UUID
        
        Returns:
            Tuple of (ExamPlan, cache_name or None)
        """
        # 1. Upload file to storage
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
                # Continue anyway, cache can still work
        
        # 2. Create cache if content is large enough
        token_count = len(state.original_content) // 4 if state.original_content else 0
        cache_name = None
        
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
            logger.info(f"Content too small ({token_count} tokens), skipping cache")
        
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
                        response = await self.llm.client.aio.models.generate_content(
                            model=cache_name,  # Cache name as model
                            contents=[{"role": "user", "parts": [{"text": prompt}]}]
                        )
                        
                        # Parse response
                        plan_text = response.text
                    
                    except Exception as cache_error:
                        # Check if cache expired
                        error_str = str(cache_error).lower()
                        if "cache" in error_str and ("not found" in error_str or "expired" in error_str or "404" in error_str):
                            logger.warning(f"Cache expired during plan generation, falling back to full content")
                            # Fallback to generation without cache
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
        
        # Use minimal prompt - content is in cache
        prompt = load_prompt(
            'planner/course_plan.txt',
            content_context="[Study materials are already loaded in context]"
        )
        
        return prompt
