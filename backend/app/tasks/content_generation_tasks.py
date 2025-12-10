"""
Unified Celery tasks for content generation.

Replaces:
- generate_exam_content
- create_exam_plan
- generate_topic_content
"""
import asyncio
from uuid import UUID
import logging

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.repositories.topic_repository import TopicRepository
from app.repositories.exam_repository import ExamRepository
from app.repositories.review_repository import ReviewItemRepository
from app.services.content_generation.topic_generator import TopicContentGenerator
from app.services.content_generation.flashcard_generator import FlashcardGenerator
from app.services.cache_fallback import CacheFallbackService
from app.agent.executor import TopicExecutor
from app.agent.quiz_generator import QuizGenerator
from app.dependencies import get_llm_provider
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name="generate_all_topics", bind=True)
def generate_all_topics(
    self,
    exam_id: str,
    user_id: str,
    cache_name: str = None
):
    """
    SINGLE Celery task for ALL content generation.
    
    Replaces:
    - generate_exam_content (old)
    - generate_topic_content (old)
    - create_exam_plan (removed)
    
    This task:
    1. Fetches topics for the exam
    2. Generates content for each topic
    3. Creates flashcards for each topic
    4. Updates progress
    5. Marks exam as ready when complete
    
    Args:
        exam_id: Exam UUID (string)
        user_id: User UUID (string)
        cache_name: Optional Gemini cache name
    """
    async def _generate():
        async with AsyncSessionLocal() as session:
            # Initialize repositories
            topic_repo = TopicRepository(session)
            exam_repo = ExamRepository(session)
            review_repo = ReviewItemRepository(session)
            
            # Get all topics for this exam
            topics = await topic_repo.get_by_exam_id(UUID(exam_id))
            topic_ids = [str(t.id) for t in topics]
            
            if not topics:
                logger.warning(f"No topics found for exam {exam_id}")
                return
            
            logger.info(
                f"Starting generation for exam {exam_id}: "
                f"{len(topic_ids)} topics, cache: {cache_name or 'none'}"
            )
            
            # Initialize LLM
            llm = get_llm_provider()
            
            # Build services
            executor = TopicExecutor(llm)
            quiz_gen = QuizGenerator(llm)
            flashcard_gen = FlashcardGenerator(quiz_gen, review_repo)
            
            # Initialize cache fallback
            from app.integrations.llm.cache_manager import ContextCacheManager
            from app.integrations.storage.supabase_storage import SupabaseStorage
            
            cache_manager = ContextCacheManager(llm)
            storage = SupabaseStorage(
                url=settings.SUPABASE_URL,
                key=settings.SUPABASE_KEY,
                bucket=settings.SUPABASE_BUCKET
            )
            fallback_service = CacheFallbackService(
                cache_manager, storage, exam_repo
            )
            
            # Build topic generator
            topic_gen = TopicContentGenerator(
                executor=executor,
                flashcard_gen=flashcard_gen,
                fallback_service=fallback_service,
                topic_repo=topic_repo,
                exam_repo=exam_repo
            )
            
            # Generate each topic
            for idx, topic_id in enumerate(topic_ids):
                try:
                    logger.info(
                        f"Generating topic {idx + 1}/{len(topic_ids)}: {topic_id}"
                    )
                    
                    await topic_gen.generate_topic(
                        topic_id=UUID(topic_id),
                        cache_name=cache_name,
                        exam_id=UUID(exam_id)
                    )
                    
                    # Update progress
                    progress = (idx + 1) / len(topic_ids)
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'progress': progress,
                            'current': idx + 1,
                            'total': len(topic_ids),
                            'topic_id': topic_id
                        }
                    )
                    
                    logger.info(
                        f"✅ Topic {idx + 1}/{len(topic_ids)} complete: {topic_id} "
                        f"({progress * 100:.1f}%)"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to generate topic {topic_id}: {e}",
                        exc_info=True
                    )
                    # Continue with other topics instead of failing entire exam
                    # Mark this topic as failed
                    try:
                        topic = await topic_repo.get_by_id(UUID(topic_id))
                        if topic:
                            topic.mark_as_failed(str(e))
                            await topic_repo.update(topic)
                            await session.commit()
                    except Exception as update_error:
                        logger.error(
                            f"Failed to mark topic as failed: {update_error}"
                        )
            
            # Mark exam as ready
            exam = await exam_repo.get_by_id(UUID(exam_id))
            if exam:
                exam.mark_as_ready()
                await exam_repo.update(exam)
                await session.commit()
                
                logger.info(f"✅ Exam {exam_id} generation complete and marked as ready")
            else:
                logger.error(f"Exam {exam_id} not found after generation")
    
    # Run async function
    try:
        asyncio.run(_generate())
        return {"status": "success", "exam_id": exam_id}
    except Exception as e:
        logger.error(f"Fatal error in generate_all_topics: {e}", exc_info=True)
        raise
