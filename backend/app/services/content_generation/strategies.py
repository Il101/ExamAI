"""
Generation strategies: Batch vs Incremental.

Strategy pattern for different content generation approaches.
"""
from abc import ABC, abstractmethod
from typing import Optional, Callable, Awaitable
from enum import Enum
import logging
import asyncio

from app.domain.exam import Exam
from app.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


class GenerationMode(Enum):
    """How to generate exam content"""
    BATCH = "batch"  # All topics at once via Celery
    INCREMENTAL = "incremental"  # On-demand as user views


class GenerationStrategy(ABC):
    """Base strategy for content generation"""
    
    @abstractmethod
    async def execute(
        self,
        exam: Exam,
        topic_generator: "TopicContentGenerator",
        progress_callback: Optional[Callable[[str, float], Awaitable[None]]] = None
    ) -> Exam:
        """
        Execute generation strategy.
        
        Args:
            exam: Exam with plan already created
            topic_generator: Generator for individual topics
            progress_callback: Optional callback for progress updates
            
        Returns:
            Updated exam
        """
        pass


class BatchStrategy(GenerationStrategy):
    """
    Generate all topics immediately via Celery.
    
    Best for:
    - Small to medium exams (< 20 topics)
    - When user wants all content ready immediately
    - When cache is available (fast generation)
    """
    
    def __init__(self, topic_repo: TopicRepository):
        """
        Initialize batch strategy.
        
        Args:
            topic_repo: Repository for fetching topics
        """
        self.topic_repo = topic_repo
    
    async def execute(
        self,
        exam: Exam,
        topic_generator: "TopicContentGenerator",
        progress_callback: Optional[Callable[[str, float], Awaitable[None]]] = None
    ) -> Exam:
        """
        Trigger Celery task to generate all topics.
        
        Returns immediately - actual generation happens in background.
        """
        from app.tasks.content_generation_tasks import generate_all_topics
        
        # Get all topics
        topics = await self.topic_repo.get_by_exam_id(exam.id)
        
        if not topics:
            logger.warning(f"No topics found for exam {exam.id}")
            return exam
        
        logger.info(
            f"Starting batch generation for exam {exam.id}: "
            f"{len(topics)} topics, cache: {exam.cache_name or 'none'}"
        )
        
        # Trigger Celery task
        task = generate_all_topics.delay(
            exam_id=str(exam.id),
            user_id=str(exam.user_id),
            topic_ids=[str(t.id) for t in topics],
            cache_name=exam.cache_name
        )
        
        logger.info(
            f"Batch generation task started: {task.id} "
            f"for exam {exam.id}"
        )
        
        return exam


class IncrementalStrategy(GenerationStrategy):
    """
    Generate topics on-demand as user views them.
    
    Best for:
    - Large exams (> 20 topics)
    - When user wants to start studying immediately
    - When cache is not available (slow generation)
    
    Prefetches first N topics, rest generated when viewed.
    """
    
    def __init__(
        self,
        topic_repo: TopicRepository,
        prefetch_count: int = 2
    ):
        """
        Initialize incremental strategy.
        
        Args:
            topic_repo: Repository for fetching topics
            prefetch_count: Number of topics to prefetch (default: 2)
        """
        self.topic_repo = topic_repo
        self.prefetch_count = prefetch_count
    
    async def execute(
        self,
        exam: Exam,
        topic_generator: "TopicContentGenerator",
        progress_callback: Optional[Callable[[str, float], Awaitable[None]]] = None
    ) -> Exam:
        """
        Prefetch first N topics, rest generated on-demand.
        
        Returns immediately - prefetch happens in background.
        """
        topics = await self.topic_repo.get_by_exam_id(exam.id)
        
        if not topics:
            logger.warning(f"No topics found for exam {exam.id}")
            return exam
        
        # Determine how many to prefetch
        prefetch_topics = topics[:self.prefetch_count]
        
        logger.info(
            f"Starting incremental generation for exam {exam.id}: "
            f"prefetching {len(prefetch_topics)}/{len(topics)} topics, "
            f"cache: {exam.cache_name or 'none'}"
        )
        
        # Generate prefetch topics in background
        for topic in prefetch_topics:
            asyncio.create_task(
                self._generate_topic_safe(
                    topic_generator=topic_generator,
                    topic_id=topic.id,
                    cache_name=exam.cache_name,
                    exam_id=exam.id
                )
            )
        
        logger.info(
            f"Incremental generation started for exam {exam.id}: "
            f"{len(prefetch_topics)} topics prefetching"
        )
        
        return exam
    
    async def _generate_topic_safe(
        self,
        topic_generator: "TopicContentGenerator",
        topic_id,
        cache_name,
        exam_id
    ):
        """Generate topic with error handling"""
        try:
            await topic_generator.generate_topic(
                topic_id=topic_id,
                cache_name=cache_name,
                exam_id=exam_id
            )
        except Exception as e:
            logger.error(
                f"Prefetch failed for topic {topic_id}: {e}",
                exc_info=True
            )
