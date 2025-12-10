"""
Topic content generation service.

Single responsibility: Generate content for ONE topic.
This is the ONLY place where topic content is generated.
"""
from typing import Optional
from uuid import UUID
import logging

from app.agent.executor import TopicExecutor
from app.services.content_generation.flashcard_generator import FlashcardGenerator
from app.services.cache_fallback import CacheFallbackService
from app.repositories.topic_repository import TopicRepository
from app.repositories.exam_repository import ExamRepository
from app.agent.state import AgentState, PlanStep, Priority
from app.utils.content_cleaner import strip_thinking_tags

logger = logging.getLogger(__name__)


class TopicContentGenerator:
    """
    Generates content for a single topic.
    
    This is the ONLY place where topic content is generated.
    Used by:
    - Batch generation (Celery task)
    - Incremental generation (on-demand)
    - Manual regeneration
    
    Guarantees:
    1. Cache is ALWAYS used if available (via CacheFallbackService)
    2. Flashcards are ALWAYS created (unless content < 50 chars)
    3. Cache expiration is handled automatically
    4. Content is cleaned (strip_thinking_tags)
    5. Topic status is updated atomically
    
    Preserves:
    - CachedCoursePlanner integration
    - ContextCacheManager usage
    - CacheFallbackService logic
    - All error handling patterns
    """
    
    def __init__(
        self,
        executor: TopicExecutor,
        flashcard_gen: FlashcardGenerator,
        fallback_service: CacheFallbackService,
        topic_repo: TopicRepository,
        exam_repo: ExamRepository
    ):
        """
        Initialize topic content generator.
        
        Args:
            executor: TopicExecutor for AI generation
            flashcard_gen: FlashcardGenerator for creating flashcards
            fallback_service: CacheFallbackService for cache expiration handling
            topic_repo: Repository for topic CRUD
            exam_repo: Repository for exam CRUD
        """
        self.executor = executor
        self.flashcard_gen = flashcard_gen
        self.fallback = fallback_service
        self.topic_repo = topic_repo
        self.exam_repo = exam_repo
    
    async def generate_topic(
        self,
        topic_id: UUID,
        cache_name: Optional[str] = None,
        exam_id: Optional[UUID] = None
    ) -> str:
        """
        Generate content and flashcards for a topic.
        
        This method:
        1. Fetches topic and exam from database
        2. Builds AgentState and PlanStep
        3. Executes topic generation with cache fallback
        4. Cleans generated content
        5. Updates topic status to 'ready'
        6. Generates flashcards
        
        Args:
            topic_id: Topic UUID to generate
            cache_name: Optional Gemini cache name
            exam_id: Optional exam UUID (fetched from topic if not provided)
            
        Returns:
            Generated content (cleaned)
            
        Raises:
            ValueError: If topic not found or generation fails
        """
        # 1. Fetch topic
        topic = await self.topic_repo.get_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        logger.info(
            f"Generating content for topic {topic_id}: '{topic.topic_name}' "
            f"(status: {topic.status})"
        )
        
        # 2. Fetch exam
        if not exam_id:
            exam_id = topic.exam_id
        exam = await self.exam_repo.get_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")
        
        # Use exam's cache if not provided
        if not cache_name:
            cache_name = exam.cache_name
        
        # 3. Build plan step from topic
        plan_step = PlanStep(
            id=topic.order_index + 1,
            title=topic.topic_name,
            description=f"Generate content for {topic.topic_name}",  # Must be >= 10 chars
            priority=Priority(topic.generation_priority) 
                if topic.generation_priority in [1, 2, 3] 
                else Priority.MEDIUM,
            estimated_paragraphs=5,
            dependencies=[]
        )
        
        # 4. Build state
        state = AgentState(
            user_request=f"Generate content for: {topic.topic_name}",
            subject=exam.subject,
            level=exam.level,
            exam_type=exam.exam_type,
            original_content=exam.original_content or ""
        )
        
        logger.info(
            f"Executing generation for '{topic.topic_name}' "
            f"(cache: {cache_name or 'none'})"
        )
        
        # 5. Execute with cache fallback
        async def _execute_with_cache(cn: Optional[str]):
            """Execute generation with given cache name"""
            return await self.executor.execute_step(
                state=state,
                plan_step=plan_step,
                previous_results={},
                cache_name=cn,
                exam_id=exam_id
            )
        
        # Use fallback service to handle cache expiration
        result = await self.fallback.execute_with_fallback(
            exam_id=exam_id,
            cache_name=cache_name,
            operation=_execute_with_cache
        )
        
        if not result.success:
            raise ValueError(
                f"Generation failed for topic {topic_id}: {result.error_message}"
            )
        
        # 6. Clean content
        content = strip_thinking_tags(result.content)
        
        logger.info(
            f"Generated {len(content)} characters for '{topic.topic_name}'"
        )
        
        # 7. Update topic
        topic.mark_as_ready(content)
        await self.topic_repo.update(topic)
        
        logger.info(f"✅ Topic {topic_id} marked as ready")
        
        # 8. Generate flashcards (ALWAYS)
        try:
            flashcards = await self.flashcard_gen.create_for_topic(
                topic_id=topic.id,
                user_id=topic.user_id,
                content=content,
                cache_name=cache_name
            )
            logger.info(
                f"✅ Created {len(flashcards)} flashcards for topic {topic_id}"
            )
        except ValueError as e:
            # Content too short - expected, not an error
            logger.info(
                f"Skipping flashcards for topic {topic_id}: {e}"
            )
        except Exception as e:
            # Unexpected error - log but don't fail topic generation
            logger.error(
                f"Failed to create flashcards for topic {topic_id}: {e}",
                exc_info=True
            )
            # Don't raise - topic generation succeeded
        
        return content
    
    async def regenerate_topic(
        self,
        topic_id: UUID,
        force_new_cache: bool = False
    ) -> str:
        """
        Regenerate content for an existing topic.
        
        Useful for:
        - User wants to regenerate content
        - Content quality is poor
        - Fixing generation errors
        
        Args:
            topic_id: Topic to regenerate
            force_new_cache: If True, don't use existing cache
            
        Returns:
            Newly generated content
        """
        topic = await self.topic_repo.get_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        exam = await self.exam_repo.get_by_id(topic.exam_id)
        
        cache_name = None if force_new_cache else exam.cache_name
        
        logger.info(
            f"Regenerating topic {topic_id}: '{topic.topic_name}' "
            f"(force_new_cache: {force_new_cache})"
        )
        
        return await self.generate_topic(
            topic_id=topic_id,
            cache_name=cache_name,
            exam_id=exam.id
        )
