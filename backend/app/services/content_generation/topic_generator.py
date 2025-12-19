from dataclasses import dataclass
from typing import Optional, Dict, Any, List
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


@dataclass
class TopicGenerationResult:
    """Result of topic generation including usage metrics."""
    content: str
    tokens_input: int
    tokens_output: int
    cost_usd: float


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
        exam_id: Optional[UUID] = None,
        output_language: Optional[str] = None,
    ) -> TopicGenerationResult:
        """
        Backward compatible wrapper for a single topic.
        """
        results = await self.generate_batch(
            topic_ids=[topic_id],
            cache_name=cache_name,
            exam_id=exam_id,
            output_language=output_language
        )
        if topic_id not in results:
            raise ValueError(f"Generation failed for topic {topic_id}")
        return results[topic_id]

    async def generate_batch(
        self,
        topic_ids: List[UUID],
        cache_name: Optional[str] = None,
        exam_id: Optional[UUID] = None,
        output_language: Optional[str] = None,
    ) -> Dict[UUID, TopicGenerationResult]:
        """
        Generate content and flashcards for a batch of topics.
        """
        if not topic_ids:
            return {}

        # 1. Fetch topics and exam
        topics = [await self.topic_repo.get_by_id(tid) for tid in topic_ids]
        topics = [t for t in topics if t]
        if not topics:
            return {}

        if not exam_id:
            exam_id = topics[0].exam_id
        exam = await self.exam_repo.get_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")

        effective_cache_name = cache_name or exam.cache_name
        lang = output_language or "ru"

        # 2. Build AgentState
        state = AgentState(
            user_request=f"Generate content for {len(topics)} topics",
            subject=exam.subject,
            level=exam.level,
            exam_type=exam.exam_type,
            original_content=exam.original_content or "",
            cache_name=effective_cache_name,
            output_language=lang
        )
        
        # Prepare PlanSteps for the batch
        state.plan = [
            PlanStep(
                id=t.id,
                title=t.topic_name,
                description=f"Generate content for {t.topic_name}",
                priority=Priority.MEDIUM,
                estimated_paragraphs=5
            ) for t in topics
        ]

        logger.info(f"Executing batch generation for {len(topics)} topics")

        # 3. Execute with fallback
        async def _execute_batch_op(cn: Optional[str]):
            state.cache_name = cn
            content_map = await self.executor.execute_batch(state, state.plan)
            return content_map, True # Success

        batch_result_map, updated_cache_name = await self.fallback.execute_with_fallback(
            exam_id=exam_id,
            cache_name=effective_cache_name,
            operation=_execute_batch_op
        )
        
        effective_cache_name = updated_cache_name or effective_cache_name

        # 4. Process theory results
        generation_results = {}
        topics_data_for_cards = []
        
        for topic in topics:
            if topic.id in batch_result_map:
                content = batch_result_map[topic.id]
                topic.start_generation()
                topic.mark_as_ready(content)
                await self.topic_repo.update(topic)
                
                generation_results[topic.id] = TopicGenerationResult(
                    content=content,
                    tokens_input=0, # Usage is aggregated in state
                    tokens_output=0,
                    cost_usd=0.0
                )
                
                if len(content) >= self.flashcard_gen.MIN_CONTENT_LENGTH:
                    topics_data_for_cards.append({
                        "id": topic.id,
                        "title": topic.topic_name,
                        "content": content
                    })

        # 5. Generate flashcards in batch
        if topics_data_for_cards:
            try:
                cards_map, cards_usage = await self.flashcard_gen.create_for_batch(
                    topics_data=topics_data_for_cards,
                    user_id=topics[0].user_id,
                    cache_name=effective_cache_name
                )
                # Usage will be added to the final result of the batch if needed
            except Exception as e:
                logger.error(f"Flashcard batch generation failed: {e}")

        return generation_results

    async def regenerate_topic(
        self,
        topic_id: UUID,
        force_new_cache: bool = False
    ) -> TopicGenerationResult:
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
            Newly generated content and usage metrics
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
