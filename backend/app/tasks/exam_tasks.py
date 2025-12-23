import asyncio
from datetime import datetime
from uuid import UUID

from celery import Task

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.llm.gemini import GeminiProvider
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository
from app.repositories.review_repository import ReviewItemRepository
from app.domain.topic import Topic
from app.services.cost_guard_service import CostGuardService
from app.services.cache_fallback import CacheFallbackService
from app.services.content_generation.topic_generator import TopicContentGenerator
from app.services.content_generation.flashcard_generator import FlashcardGenerator
from app.services.content_generation.summary_generator import ExamSummaryGenerator, TopicGist
from app.integrations.storage.supabase_storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager
from app.services.study_planner_service import StudyPlannerService
from app.tasks.celery_app import celery_app
from google import genai
from google.genai import types

from app.agent.executor import TopicExecutor
from app.agent.quiz_generator import QuizGenerator


# Global semaphore to limit concurrent LLM calls across ALL workers
# This prevents request spikes when multiple Celery workers generate exams in parallel
# Tier 1: 1,000 RPM, 1,000,000 TPM
# Limit: 15 concurrent API calls (conservative for Tier 1, allows ~900 RPM headroom)
_llm_call_semaphore = asyncio.Semaphore(15)


def get_llm_provider():
    """Helper to create LLM provider instance"""
    return GeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        fallback_model=settings.GEMINI_FALLBACK_MODEL,
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

    async def _close_session(self):
        if self._db_session:
            await self._db_session.close()
            self._db_session = None

    def after_return(self, *args, **kwargs):
        """Close database session after task completes"""
        if self._db_session is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._close_session())
                else:
                    loop.run_until_complete(self._close_session())
            except Exception:
                pass


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
    # Reset LLM request counter for this run to provide accurate per-exam metrics
    GeminiProvider.reset_request_count()
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
        print(f"[CELERY ASYNC] Creating first GeminiProvider instance...")
        llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL, fallback_model=settings.GEMINI_FALLBACK_MODEL)
        print(f"[CELERY ASYNC] First GeminiProvider created successfully")

        print(f"[CELERY ASYNC] Creating executor services...")
        executor = TopicExecutor(llm)
        quiz_gen = QuizGenerator(llm)
        flashcard_gen = FlashcardGenerator(quiz_gen, review_repo)
        print(f"[CELERY ASYNC] Executor services created successfully")

        print(f"[CELERY ASYNC] Creating storage service...")
        storage = SupabaseStorage(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_KEY,
            bucket=settings.SUPABASE_BUCKET,
        )
        print(f"[CELERY ASYNC] Storage service created successfully")
        
        # Initialize GeminiProvider (centralized logic)
        print(f"[CELERY ASYNC] Creating second GeminiProvider instance...")
        llm_provider = GeminiProvider(api_key=settings.GEMINI_API_KEY)
        print(f"[CELERY ASYNC] Second GeminiProvider created successfully")
        
        # Initialize helper services
        print(f"[CELERY ASYNC] Creating cache manager...")
        cache_manager = ContextCacheManager(llm_provider)
        print(f"[CELERY ASYNC] Cache manager created successfully")
        
        print(f"[CELERY ASYNC] Creating fallback service...")
        fallback_service = CacheFallbackService(storage, cache_manager)
        print(f"[CELERY ASYNC] Fallback service created successfully")

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
            
        # 0. Study Scheduling (New)
        if exam.exam_date:
            print(f"[CELERY ASYNC] Scheduling topics for exam {exam_id} (exam_date={exam.exam_date})...")
            planner = StudyPlannerService()
            topics = planner.schedule_exam(exam, topics)
            # Save scheduled dates
            for topic in topics:
                await topic_repo.update(topic)
            await session.commit()
            print(f"[CELERY ASYNC] Successfully scheduled {total} topics.")

        # Ensure exam is in generating state
        if exam.status != "generating":
            exam.start_generation()
            await exam_repo.update(exam)
            await session.commit()

        # 1. Dynamic Initial Batch Size (based on complexity)
        # We aim for ~10-15 paragraphs per batch to avoid LLM saturation/truncation
        # Medium topics (5 para) -> batch of 3. Simple (3 para) -> batch of 5.
        avg_complexity = 5.0 # Default
        if pending_topics:
            # We don't have direct 'estimated_paragraphs' in DB topic objects here, 
            # but we can check if it's a 'main' topic or use a default.
            # For now, let's use a conservative smart default:
            batch_size = 4
            if any(len(t.topic_name) > 50 for t in pending_topics): # Very long names often mean complex topics
                batch_size = 3
        else:
            batch_size = 4

        # Split pending topics into batches
        batches = [pending_topics[i : i + batch_size] for i in range(0, len(pending_topics), batch_size)]
        
        total_in = 0
        total_out = 0
        total_cost = 0.0
        
        for batch_idx, batch in enumerate(batches):
            batch_names = ", ".join([t.topic_name for t in batch])
            await progress_callback(
                f"Generating Batch {batch_idx + 1}/{len(batches)}: {batch_names}",
                (ready_count) / total,
            )

            try:
                # Use semaphore to limit concurrent LLM calls
                async with _llm_call_semaphore:
                    print(f"[PIPELINE] Calling generate_batch for {len(batch)} topics. Model: {settings.GEMINI_MODEL}")
                    # Execute batch generation
                    batch_out = await topic_gen.generate_batch(
                        topic_ids=[t.id for t in batch],
                        cache_name=exam.cache_name,
                        exam_id=exam.id,
                        output_language=getattr(user, "preferred_language", None),
                    )
                    batch_results = batch_out.get("results", {})
                    batch_usage = batch_out.get("usage", {})

                # Update counts and log
                for t in batch:
                    if t.id in batch_results:
                        ready_count += 1
                
                # Aggregate usage metrics
                total_in += batch_usage.get("tokens_input", 0)
                total_out += batch_usage.get("tokens_output", 0)
                total_cost += batch_usage.get("cost_usd", 0.0)
                
                # Explicit commit after batch success
                await session.commit()
                print(f"[PIPELINE] batch_done idx={batch_idx+1}/{len(batches)} topics={len(batch)} batch_cost=${batch_usage.get('cost_usd', 0):.4f}")
                
            except Exception as e:
                import sys
                import traceback
                err = f"[PIPELINE] batch_failed idx={batch_idx+1}/{len(batches)} error={e}\n{traceback.format_exc()}"
                print(err)
                sys.stderr.write(err + "\n")
                sys.stderr.flush()
                
                # If batch failing, try to mark them best-effort
                for t in batch:
                    try:
                        fresh = await topic_repo.get_by_id(t.id)
                        if fresh and fresh.status != "ready":
                            fresh.mark_as_failed(str(e))
                            await topic_repo.update(fresh)
                    except: pass
                await session.commit()
                await session.commit()

        # Mark exam ready even if some topics failed; summary reflects success ratio.
        summary = f"Generated {ready_count}/{total} topics successfully"

        # Generate a short TL;DR for frontend display.
        # Best-effort: if it fails, we fall back to the progress-style summary above.
        try:
            fresh_topics = await topic_repo.get_by_exam_id(exam_id)
            ready_topics = [t for t in fresh_topics if t.status == "ready" and (t.content or "").strip()]

            # Cap input to prevent very large prompts.
            ready_topics = ready_topics[:20]

            summary_gen = ExamSummaryGenerator(llm)
            tldr, summary_usage = await summary_gen.generate_tldr(
                subject=exam.subject,
                exam_type=exam.exam_type,
                level=exam.level,
                topics=[TopicGist(title=t.topic_name, content=t.content or "") for t in ready_topics],
                total_count=total,
                ready_count=ready_count,
                output_language=getattr(user, "preferred_language", None),
                cache_name=exam.cache_name,
            )
            
            # Aggregate summary usage
            total_in += summary_usage.get("tokens_input", 0)
            total_out += summary_usage.get("tokens_output", 0)
            total_cost += summary_usage.get("cost_usd", 0.0)
            if tldr and len(tldr.strip()) > 0:  # Only use if non-empty
                summary = tldr
            else:
                print(f"[PIPELINE] tldr_empty exam_id={exam_id}, using fallback")
        except Exception as e:
            print(f"[PIPELINE] tldr_failed exam_id={exam_id} error_type={type(e).__name__} error={e}")

        exam.mark_as_ready(
            ai_summary=summary,
            token_input=total_in,
            token_output=total_out,
            cost=total_cost,
        )
        await exam_repo.update(exam)
        await session.commit()

        # Trigger email notification if enabled
        if getattr(user, "notification_exam_ready", True):
            from app.tasks.email_tasks import send_exam_ready_notification, send_user_push_notification

            send_exam_ready_notification.delay(
                user_email=user.email, exam_title=exam.title, exam_id=str(exam_id)
            )
            
            send_user_push_notification.delay(
                user_id=str(user.id),
                title="Your study notes are ready! 📚",
                body=f"Study materials for '{exam.title}' have been generated.",
                url=f"/exams/{exam_id}"
            )

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
            cache_name=exam.cache_name,
        )

        state.output_language = getattr(user, "preferred_language", None) or "ru"
        
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

