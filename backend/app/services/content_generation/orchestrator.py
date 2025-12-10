"""
Content generation orchestrator.

Central coordinator for ALL content generation.
Decides strategy and coordinates topic generation.
"""
from typing import Optional, Callable, Awaitable
from enum import Enum
import logging

from app.domain.exam import Exam
from app.services.content_generation.topic_generator import TopicContentGenerator
from app.services.content_generation.strategies import (
    GenerationStrategy,
    BatchStrategy,
    IncrementalStrategy,
    GenerationMode
)

logger = logging.getLogger(__name__)


class ContentGenerationOrchestrator:
    """
    Central orchestrator for ALL content generation.
    
    Responsibilities:
    1. Decide generation strategy (batch vs incremental)
    2. Coordinate topic generation
    3. Handle progress tracking
    4. Ensure flashcards are created
    
    This replaces:
    - AgentService.generate_exam_content (partially)
    - GenerationService
    - Multiple Celery tasks
    """
    
    def __init__(
        self,
        topic_generator: TopicContentGenerator,
        batch_strategy: BatchStrategy,
        incremental_strategy: IncrementalStrategy
    ):
        """
        Initialize orchestrator.
        
        Args:
            topic_generator: Generator for individual topics
            batch_strategy: Strategy for batch generation
            incremental_strategy: Strategy for incremental generation
        """
        self.topic_generator = topic_generator
        self.batch = batch_strategy
        self.incremental = incremental_strategy
    
    async def generate_exam_content(
        self,
        exam: Exam,
        mode: GenerationMode = GenerationMode.BATCH,
        progress_callback: Optional[Callable[[str, float], Awaitable[None]]] = None
    ) -> Exam:
        """
        Generate content for entire exam.
        
        This is the MAIN entry point for content generation.
        
        Args:
            exam: Exam with plan already created (topics exist in DB)
            mode: How to generate (batch or incremental)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Updated exam
            
        Raises:
            ValueError: If exam has no topics or invalid status
        """
        # Validate exam
        if not exam.can_generate():
            raise ValueError(
                f"Cannot generate exam with status: {exam.status}, "
                f"topic_count: {exam.topic_count}"
            )
        
        logger.info(
            f"Starting content generation for exam {exam.id}: "
            f"mode={mode.value}, topics={exam.topic_count}, "
            f"cache={exam.cache_name or 'none'}"
        )
        
        # Select strategy
        strategy = self.batch if mode == GenerationMode.BATCH else self.incremental
        
        # Execute strategy
        updated_exam = await strategy.execute(
            exam=exam,
            topic_generator=self.topic_generator,
            progress_callback=progress_callback
        )
        
        logger.info(
            f"Content generation initiated for exam {exam.id} "
            f"using {mode.value} strategy"
        )
        
        return updated_exam
    
    async def generate_single_topic(
        self,
        topic_id,
        cache_name: Optional[str] = None
    ) -> None:
        """
        Generate content for single topic.
        
        Used for:
        - Incremental generation (on-demand)
        - Manual regeneration
        - Progressive viewing
        
        Args:
            topic_id: Topic UUID to generate
            cache_name: Optional cache name
        """
        logger.info(
            f"Generating single topic {topic_id} "
            f"(cache: {cache_name or 'none'})"
        )
        
        await self.topic_generator.generate_topic(
            topic_id=topic_id,
            cache_name=cache_name
        )
        
        logger.info(f"✅ Single topic generation complete: {topic_id}")
