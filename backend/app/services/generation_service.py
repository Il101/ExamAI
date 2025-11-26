"""Generation service with block-aware prefetch logic"""
from typing import Optional
from uuid import UUID
import asyncio
import logging

from app.agent.schemas import ExamPlan, TopicPlan
from app.agent.cached_executor import CachedTopicExecutor
from app.services.prefetch_manager import PrefetchManager
from app.services.cache_fallback import CacheFallbackService

logger = logging.getLogger(__name__)


class GenerationService:
    """Manages topic generation with smart prefetching"""
    
    def __init__(
        self,
        executor: CachedTopicExecutor,
        prefetch_manager: PrefetchManager,
        fallback_service: CacheFallbackService
    ):
        self.executor = executor
        self.prefetch = prefetch_manager
        self.fallback = fallback_service
    
    async def prefetch_initial_topics(
        self,
        exam_id: UUID,
        plan: ExamPlan,
        cache_name: Optional[str]
    ) -> None:
        """
        Prefetch first 2 topics of first block
        
        Args:
            exam_id: Exam UUID
            plan: Complete exam plan
            cache_name: Cache identifier
        """
        if not plan.blocks:
            logger.warning(f"No blocks in plan for exam {exam_id}")
            return
        
        first_block = plan.blocks[0]
        topics_to_prefetch = first_block.topics[:2]
        
        logger.info(f"Prefetching {len(topics_to_prefetch)} topics for exam {exam_id}")
        
        for topic in topics_to_prefetch:
            self.prefetch.set_generating(exam_id, topic.id)
            
            # Generate in background
            asyncio.create_task(
                self._generate_and_store(exam_id, topic, cache_name)
            )
    
    async def _generate_and_store(
        self,
        exam_id: UUID,
        topic: TopicPlan,
        cache_name: Optional[str]
    ) -> None:
        """Generate topic and store in Redis"""
        try:
            content = await self.executor.execute_topic_with_cache(
                topic=topic,
                cache_name=cache_name,
                exam_id=exam_id,
                fallback_service=self.fallback
            )
            self.prefetch.set_completed(exam_id, topic.id, content)
            logger.info(f"Prefetch completed for {topic.id}")
        except Exception as e:
            logger.error(f"Prefetch failed for {topic.id}: {e}")
            self.prefetch.set_failed(exam_id, topic.id, str(e))
    
    async def trigger_next_block(
        self,
        exam_id: UUID,
        current_topic_id: str,
        plan: ExamPlan,
        cache_name: Optional[str]
    ) -> None:
        """
        Generate next block when user reaches last topic of current block
        
        Args:
            exam_id: Exam UUID
            current_topic_id: Topic user is viewing
            plan: Complete exam plan
            cache_name: Cache identifier
        """
        # Find current block and topic position
        for i, block in enumerate(plan.blocks):
            topic_ids = [t.id for t in block.topics]
            if current_topic_id in topic_ids:
                # Is this the last topic in block?
                if topic_ids[-1] == current_topic_id:
                    # Generate next block if exists
                    if i + 1 < len(plan.blocks):
                        next_block = plan.blocks[i + 1]
                        logger.info(f"Triggering generation for next block: {next_block.block_title}")
                        
                        for topic in next_block.topics:
                            # Check if already generated
                            status = self.prefetch.get_status(exam_id, topic.id)
                            if not status:
                                asyncio.create_task(
                                    self._generate_and_store(exam_id, topic, cache_name)
                                )
                break
    
    async def get_topic_content(
        self,
        exam_id: UUID,
        topic_id: str,
        topic: TopicPlan,
        cache_name: Optional[str]
    ) -> str:
        """
        Get topic content (from prefetch or generate on-demand)
        
        Args:
            exam_id: Exam UUID
            topic_id: Topic identifier
            topic: Topic plan
            cache_name: Cache identifier
        
        Returns:
            Generated markdown content
        """
        # Check prefetch first
        content = self.prefetch.get_content(exam_id, topic_id)
        if content:
            logger.info(f"Using prefetched content for {topic_id}")
            return content
        
        # Generate on-demand
        logger.info(f"Generating on-demand for {topic_id}")
        content = await self.executor.execute_topic_with_cache(
            topic=topic,
            cache_name=cache_name,
            exam_id=exam_id,
            fallback_service=self.fallback
        )
        
        return content
