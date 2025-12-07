"""Cache-aware executor for topic generation"""
from typing import Optional
from uuid import UUID

from app.agent.executor import TopicExecutor
from app.agent.state import AgentState
from app.agent.schemas import TopicPlan
from app.services.cache_fallback import CacheFallbackService
import logging

logger = logging.getLogger(__name__)


class CachedTopicExecutor(TopicExecutor):
    """Executor with cache support and automatic fallback"""

    def __init__(self, llm_provider, fallback_service: Optional[CacheFallbackService] = None):
        super().__init__(llm_provider)
        self.fallback_service = fallback_service

    
    async def execute_step(self, state: AgentState) -> str:
        """
        Execute step using Gemini Cache if available.
        Overrides base TopicExecutor.execute_step.
        """
        current_step = state.get_current_step()
        if not current_step:
            raise ValueError("No current step to execute")
            
        print(f"[CachedExecutor] Generating topic {current_step.id} using cache: {state.cache_name}")
        
        # Build context from previous results
        # We access private method from base class - this is fine in Python
        context = self._build_previous_context(state, current_step)
        
        # Determine fallback service
        # For now, we don't injecting fallback service here, 
        # but we could add it to AgentState in future.
        # CachedTopicExecutor checks for fallback service passed in execute_topic_with_cache.
        # But we are calling execute_step which doesn't take fallback service.
        # That's okay, execute_topic_with_cache handles None fallback service (simple cache usage).
        
        return await self.execute_topic_with_cache(
            topic=current_step,
            cache_name=state.cache_name,
            exam_id=UUID(state.exam_id) if state.exam_id else None,
            fallback_service=self.fallback_service,
            context=context
        )

    async def execute_topic_with_cache(
        self,
        topic: TopicPlan,
        cache_name: Optional[str],
        exam_id: UUID,
        fallback_service: Optional[CacheFallbackService] = None,
        context: str = ""
    ) -> str:
        """
        Generate topic content using cache
        
        Args:
            topic: Topic to generate
            cache_name: Cache identifier (or None for no cache)
            exam_id: Exam UUID for fallback
            fallback_service: Fallback service for cache recreation
            context: Additional context from previous topics
        
        Returns:
            Generated markdown content
        """
        prompt = self._build_topic_prompt(topic, context, cache_name)
        
        # Log the prompt for debugging
        logger.info(f"[CachedExecutor] Topic prompt (first 500 chars): {prompt[:500]}...")
        logger.info(f"[CachedExecutor] Using cache: {cache_name is not None}, Cache name: {cache_name}")
        
        async def generate_op(cache: Optional[str]):
            """Operation to execute with cache"""
            if cache:
                # Use cached content by passing cache name in config
                # This is the correct API for Gemini context caching
                from app.core.config import settings
                try:
                    response = await self.llm.client.aio.models.generate_content(
                        model=settings.GEMINI_MODEL,  # Use base model
                        config={
                            "cached_content": cache,
                        },
                        contents=[{"role": "user", "parts": [{"text": prompt}]}]
                    )
                    return response.text
                except Exception as e:
                    logger.error(f"[CachedExecutor] API Error: {type(e).__name__}: {str(e)}")
                    logger.error(f"[CachedExecutor] Cache name: {cache}")
                    logger.error(f"[CachedExecutor] Model: {settings.GEMINI_MODEL}")
                    # Check if it's a 403 error
                    error_str = str(e).lower()
                    if "403" in error_str or "forbidden" in error_str:
                        logger.error("[CachedExecutor] 403 Forbidden - possible causes:")
                        logger.error("  1. API key invalid or expired")
                        logger.error("  2. Billing not enabled")
                        logger.error("  3. Rate limit exceeded")
                        logger.error("  4. Cache expired or invalid")
                    raise
            else:
                # Fallback: regular generation without max_tokens limit
                response = await self.llm.generate(prompt)
                return response.content
        
        # Execute with fallback if available
        if fallback_service and cache_name:
            return await fallback_service.execute_with_fallback(
                exam_id, cache_name, generate_op
            )
        else:
            return await generate_op(cache_name)
    
    def _build_topic_prompt(self, topic: TopicPlan, context: str = "", cache_name: Optional[str] = None) -> str:
        """Build prompt for topic generation"""
        
        # Add explicit cache instruction if using cache
        cache_instruction = ""
        if cache_name:
            cache_instruction = """
**SOURCE MATERIALS:**
The user's study materials (PDF, documents, or text) are already loaded in the context cache.
You MUST analyze and extract information from these cached materials to create the study notes.
DO NOT make up information - use only what's in the cached source materials.

"""
        
        return f"""{cache_instruction}Generate structured study notes for this topic.

**Topic:** {topic.title}
**Description:** {topic.description}
**Target Length:** {topic.estimated_paragraphs} well-structured paragraphs

{context}

**FORMATTING REQUIREMENTS (CRITICAL):**
1. **Use headings:** Start with `###` for subsections
2. **Use bullet points:** Prefer `-` lists over long paragraphs
3. **Use numbered lists:** For steps, procedures, rankings
4. **Use tables:** For comparisons, formulas, data
5. **Keep paragraphs SHORT:** 2-4 sentences maximum
6. **Use bold** for key terms
7. **Break up text:** Use horizontal rules `---` between major concepts
8. **Add examples in code blocks:** Use ``` for code, formulas, or structured data
9. **Use blockquotes** for important notes: `> **Note:** ...`
10. **NO PLACEHOLDERS:** Never write `[Insert X Here]` - use actual content from materials

**Content Structure:**
1. Brief introduction (1-2 sentences)
2. Key concepts with bullet points
3. Detailed explanation with subheadings
4. Examples or practice problems
5. Common mistakes to avoid
6. Quick summary at the end

**IMPORTANT:**
- Extract REAL information from the source materials in cache
- If materials don't contain specific info for this topic, make reasonable educational content
- NEVER use placeholder text like `[Insert Definition]`
- Keep it scannable - students should grasp key points in 30 seconds

Generate structured study notes now:"""
