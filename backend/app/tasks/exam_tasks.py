import asyncio
from datetime import datetime
from uuid import UUID

from celery import Task

from app.agent.orchestrator import PlanAndExecuteAgent
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.llm.gemini import GeminiProvider
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository
from app.repositories.review_repository import ReviewItemRepository
from app.domain.topic import Topic
from app.services.agent_service import AgentService
from app.services.cost_guard_service import CostGuardService
from app.services.cache_fallback import CacheFallbackService
from app.services.content_generation.topic_generator import TopicContentGenerator
from app.services.content_generation.flashcard_generator import FlashcardGenerator
from app.integrations.storage.supabase_storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager
from app.tasks.celery_app import celery_app
from google import genai

from app.agent.executor import TopicExecutor
from app.agent.quiz_generator import QuizGenerator


def get_llm_provider():
    """Helper to create LLM provider instance"""
    return GeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
    )


class ExamGenerationTask(Task):
    """
    Custom task class with database session management.
    """

    _db_session = None

    @property
    def db_session(self):
        if self._db_session is None:
            self._db_session = AsyncSessionLocal()
        return self._db_session

    def after_return(self, *args, **kwargs):
        """Close database session after task completes"""
        if self._db_session is not None:
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule coroutine
                    loop.create_task(self._db_session.close())
                else:
                    # If loop is not running, use asyncio.run
                    asyncio.run(self._db_session.close())
            except RuntimeError:
                # Event loop is closed, ignore
                pass
            finally:
                self._db_session = None


@celery_app.task(
    bind=True,
    base=ExamGenerationTask,
    name="generate_exam_content",
    max_retries=3,
    default_retry_delay=60,
)
def generate_exam_content(self, exam_id: str, user_id: str):
    """
    Celery task for generating exam content with AI.

    Args:
        exam_id: UUID of exam to generate
        user_id: UUID of user who owns the exam

    This is the EXECUTION phase of progressive generation.
    It assumes the exam is already PLANNED (has topics).
    1. Gets exam and topics from database
    2. Generates content for each pending topic
    3. Finalizes the exam
    """

    print(f"[CELERY] Starting generate_exam_content task for exam_id={exam_id}, user_id={user_id}")
    print("[PIPELINE] marker=generate_exam_content.v1")
    print(f"[CELERY] Task ID: {self.request.id}")
    
    async def task_wrapper():
        try:
            print(f"[CELERY] Running async generation...")
            # Run async code
            result = await _generate_exam_content_async(
                exam_id=UUID(exam_id), user_id=UUID(user_id), task=self
            )
            print(f"[CELERY] Generation completed successfully for exam {exam_id}")
            
            # Log API metrics summary
            from app.integrations.llm.metrics import log_metrics_summary
            log_metrics_summary()
            
            return result
            
        except Exception as e:
            # Catch error within the same event loop
            # Categorize error and create user-friendly message
            error_category, user_message = _categorize_error(e)

            # Log detailed error for developers (CRITICAL: Force to stderr)
            import sys
            import traceback
            error_details = f"""
[CELERY ERROR] ❌ Generation failed for exam {exam_id}
Error Type: {type(e).__name__}
Error Category: {error_category}
Error Message: {str(e)}
User Message: {user_message}
Traceback:
{traceback.format_exc()}
"""
            print(error_details)
            sys.stderr.write(error_details)
            sys.stderr.flush()

            # Mark exam as failed with descriptive error message
            # Safe to call directly as we are in the same loop
            try:
                await _mark_exam_failed(
                    UUID(exam_id), error_category=error_category, error_message=user_message
                )
            except Exception as mark_error:
                print(f"[CELERY] CRITICAL: Failed to mark exam as failed: {mark_error}")
                sys.stderr.write(f"[CELERY] CRITICAL: Failed to mark exam as failed: {mark_error}\n")
                sys.stderr.flush()

            # Retry task if retries remaining (only for transient errors)
            if self.request.retries < self.max_retries and error_category in [
                "api_error",
                "timeout",
            ]:
                # We need to raise Retry exception, but we are inside async wrapper.
                # asyncio.run will propagate exceptions.
                # Wait, self.retry raises an exception.
                raise self.retry(exc=e)

            raise e

    # Run the wrapper in a single event loop
    return asyncio.run(task_wrapper())


def _categorize_error(exception: Exception) -> tuple[str, str]:
    """
    Categorize exception and create user-friendly error message.

    Returns:
        (error_category, user_facing_message)
    """
    error_str = str(exception).lower()

    # Exam status errors (already completed, etc.) - should NOT retry
    if "cannot generate exam with status" in error_str or "status: ready" in error_str:
        return (
            "exam_already_completed",
            "This exam has already been generated and is ready to use.",
        )

    # File parsing errors
    if "parse" in error_str or "encoding" in error_str:
        return (
            "file_parsing_error",
            "Unable to parse the uploaded file. Please ensure it's a valid PDF, DOCX, or TXT file and try again.",
        )

    # Token/budget errors
    if "token" in error_str or "budget" in error_str or "limit" in error_str:
        return (
            "budget_exceeded",
            "Generation would exceed your daily usage limit. Please upgrade your plan or try again tomorrow.",
        )

    # API/LLM errors
    if "api" in error_str or "gemini" in error_str or "rate" in error_str:
        return (
            "api_error",
            "Temporary issue with AI service. We'll retry automatically. If this persists, please contact support.",
        )

    # Timeout errors
    if "timeout" in error_str or "timed out" in error_str:
        return (
            "timeout",
            "Generation took too long and was cancelled. Try uploading a smaller file or reducing complexity.",
        )

    # Validation errors
    if "validation" in error_str or "invalid" in error_str:
        return (
            "validation_error",
            "The input data is invalid. Please check your subject, exam type, and uploaded materials.",
        )

    # Default: unknown error
    return (
        "unknown_error",
        "An unexpected error occurred. Our team has been notified. Please try again or contact support if this persists.",
    )


async def _generate_exam_content_async(
    exam_id: UUID, user_id: UUID, task: Task
) -> dict:
    """
    Async implementation of exam content generation.
    """
    print(f"[CELERY ASYNC] Starting async generation for exam {exam_id}")
    print("[PIPELINE] marker=_generate_exam_content_async.v1")
    
    async with AsyncSessionLocal() as session:
        print(f"[CELERY ASYNC] Session created, initializing repositories...")
        # Initialize repositories
        exam_repo = ExamRepository(session)
        topic_repo = TopicRepository(session)
        user_repo = UserRepository(session)
        review_repo = ReviewItemRepository(session)

        print(f"[CELERY ASYNC] Fetching user and exam from database...")
        # Get user and exam with timeout to prevent hanging
        try:
            user = await asyncio.wait_for(
                user_repo.get_by_id(user_id),
                timeout=30.0  # 30 second timeout
            )
            exam = await asyncio.wait_for(
                exam_repo.get_by_id(exam_id),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise ValueError(f"Database query timeout: failed to fetch user or exam after 30s")

        if not user or not exam:
            raise ValueError("User or exam not found")

        print(f"[CELERY ASYNC] User and exam found. Initializing generation services...")

        # Always use the unified TopicContentGenerator flow here so that:
        # - topic state machine remains consistent (pending/failed -> generating -> ready/failed)
        # - flashcards are generated via FlashcardGenerator (and not skipped silently)
        # - cache fallback behavior is consistent
        llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)

        executor = TopicExecutor(llm)
        quiz_gen = QuizGenerator(llm)
        flashcard_gen = FlashcardGenerator(quiz_gen, review_repo)

        storage = SupabaseStorage(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_KEY,
            bucket=settings.SUPABASE_BUCKET,
        )
        genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        cache_manager = ContextCacheManager(genai_client)
        fallback_service = CacheFallbackService(storage, cache_manager)

        topic_gen = TopicContentGenerator(
            executor=executor,
            flashcard_gen=flashcard_gen,
            fallback_service=fallback_service,
            topic_repo=topic_repo,
            exam_repo=exam_repo,
        )

        # Progress callback to update Celery task state
        async def progress_callback(message: str, progress: float):
            task.update_state(
                state="PROGRESS",
                meta={"current": int(progress * 100), "total": 100, "status": message},
            )

        print(f"[CELERY ASYNC] Starting unified per-topic generation...")

        topics = await topic_repo.get_by_exam_id(exam_id)
        total = len(topics)
        if total == 0:
            raise ValueError(f"No topics found for exam {exam_id}")

        # Ensure exam is in generating state
        if exam.status != "generating":
            exam.start_generation()
            await exam_repo.update(exam)
            await session.commit()

        # Generate sequentially to avoid rate-limit bursts
        ready_count = 0
        for idx, topic in enumerate(topics):
            # Skip already-ready topics to support resume
            if topic.status == "ready" and topic.content:
                ready_count += 1
                continue

            step_progress = (idx + 1) / total
            await progress_callback(
                f"Generating: {topic.topic_name}",
                step_progress,
            )

            try:
                await topic_gen.generate_topic(
                    topic_id=topic.id,
                    cache_name=exam.cache_name,
                    exam_id=exam.id,
                )
                # CRITICAL: TopicContentGenerator updates are not guaranteed to
                # commit automatically. Without an explicit commit here,
                # generation can appear successful in logs while topics remain
                # pending/empty in the DB.
                await session.commit()
                ready_count += 1
            except Exception as e:
                # TopicContentGenerator may fail before topic.start_generation() is called.
                # Mark failure best-effort without breaking the whole exam.
                try:
                    fresh = await topic_repo.get_by_id(topic.id)
                    if fresh and fresh.status == "generating":
                        fresh.mark_as_failed(str(e))
                        await topic_repo.update(fresh)
                        await session.commit()
                except Exception:
                    pass

        # Mark exam ready even if some topics failed; summary reflects success ratio.
        summary = f"Generated {ready_count}/{total} topics successfully"
        exam.mark_as_ready(
            ai_summary=summary,
            token_input=0,
            token_output=0,
            cost=0.0,
        )
        await exam_repo.update(exam)
        await session.commit()

        return {
            "status": "success",
            "exam_id": str(exam_id),
            "topic_count": total,
            "ready_topics": ready_count,
        }


async def _mark_exam_failed(
    exam_id: UUID,
    error_category: str = "unknown_error",
    error_message: str = "An error occurred during generation",
):
    """
    Mark exam as failed with detailed error information.

    Args:
        exam_id: Exam UUID
        error_category: Category of error (file_parsing_error, budget_exceeded, etc.)
        error_message: User-friendly error message
    """
    async with AsyncSessionLocal() as session:
        exam_repo = ExamRepository(session)
        exam = await exam_repo.get_by_id(exam_id)

        if exam:
            # Store error details for user feedback
            exam.mark_as_failed()

            # Best-effort: not all domain models expose these fields.
            # Keep assignments guarded to avoid runtime/type errors.
            for attr_name, attr_value in (
                ("error_category", error_category),
                ("error_message", error_message),
                ("failed_at", datetime.utcnow()),
            ):
                if hasattr(exam, attr_name):
                    setattr(exam, attr_name, attr_value)

            await exam_repo.update(exam)
            await session.commit()


@celery_app.task(
    bind=True,
    name="generate_topic_content",
    base=ExamGenerationTask,
    max_retries=3,
    default_retry_delay=60,
)
def generate_topic_content(self, topic_id: str, user_id: str):
    """Generate content for a single topic (progressive generation step 2)"""
    try:
        asyncio.run(
            _generate_topic_content_async(
                topic_id=UUID(topic_id),
                user_id=UUID(user_id),
            )
        )
        return {"status": "success", "topic_id": topic_id}
    except Exception as e:
        error_category, user_message = _categorize_error(e)
        asyncio.run(_mark_topic_failed(UUID(topic_id), user_message))
        
        if self.request.retries < self.max_retries and error_category in ["api_error", "timeout"]:
            raise self.retry(exc=e)
        raise


async def _generate_topic_content_async(topic_id: UUID, user_id: UUID):
    """Async implementation of topic content generation"""
    async with AsyncSessionLocal() as session:
        topic_repo = TopicRepository(session)
        exam_repo = ExamRepository(session)
        user_repo = UserRepository(session)
        
        topic = await topic_repo.get_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        exam = await exam_repo.get_by_id(topic.exam_id)
        user = await user_repo.get_by_id(user_id)

        if not exam:
            raise ValueError(f"Exam {topic.exam_id} not found for topic {topic_id}")
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        llm_provider = get_llm_provider()
        cost_guard = CostGuardService(session)

        from app.agent.state import AgentState, PlanStep, Priority
        
        # Ensure topic is in generating state
        topic.start_generation()
        await topic_repo.update(topic)
        
        state = AgentState(
            user_request=f"Generate content for topic: {topic.topic_name}",
            subject=exam.subject,
            level=exam.level,
            exam_type=exam.exam_type,
            original_content=exam.original_content,
        )
        
        plan_step = PlanStep(
            id=topic.order_index + 1,
            title=topic.topic_name,
            description=f"Generate content for topic: {topic.topic_name}",
            priority=Priority(topic.generation_priority) if topic.generation_priority in [1,2,3] else Priority.MEDIUM,
            estimated_paragraphs=5,
            dependencies=[],
        )
        
        
        state.plan = [plan_step]
        state.current_step_index = 0
        
        executor = TopicExecutor(llm_provider)
        # execute_step returns str directly and raises detailed exceptions on failure
        content = await executor.execute_step(state)
        
        topic.mark_as_ready(content)
        await topic_repo.update(topic)
        
        await cost_guard.log_usage(
            user_id=user.id,
            model_name=settings.GEMINI_MODEL,
            provider="gemini",
            operation_type="topic_generation",
            input_tokens=state.total_tokens_used // 2,
            output_tokens=state.total_tokens_used // 2,
            cost_usd=state.total_cost_usd,
        )
        
        await session.commit()


async def _mark_topic_failed(topic_id: UUID, error_message: str):
    """Mark topic as failed"""
    async with AsyncSessionLocal() as session:
        topic_repo = TopicRepository(session)
        topic = await topic_repo.get_by_id(topic_id)
        if topic:
            topic.mark_as_failed(error_message)
            await topic_repo.update(topic)
            await session.commit()

