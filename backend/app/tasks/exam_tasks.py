from celery import Task
from uuid import UUID
import asyncio
from typing import Optional
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.user_repository import UserRepository
from app.services.cost_guard_service import CostGuardService
from app.services.agent_service import AgentService
from app.integrations.llm.gemini import GeminiProvider
from app.agent.orchestrator import PlanAndExecuteAgent
from app.core.config import settings


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
            asyncio.run(self._db_session.close())
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

    This is a long-running task that:
    1. Gets exam from database
    2. Runs AI agent (Plan → Execute → Finalize)
    3. Saves results to database
    4. Updates exam status
    """

    try:
        # Run async code in sync Celery task
        result = asyncio.run(
            _generate_exam_content_async(
                exam_id=UUID(exam_id), user_id=UUID(user_id), task=self
            )
        )

        return result

    except Exception as e:
        # Categorize error and create user-friendly message
        error_category, user_message = _categorize_error(e)

        # Log detailed error for developers
        print(f"Error generating exam {exam_id}: {str(e)}")
        print(f"Error category: {error_category}")

        # Mark exam as failed with descriptive error message
        asyncio.run(
            _mark_exam_failed(
                UUID(exam_id), error_category=error_category, error_message=user_message
            )
        )

        # Retry task if retries remaining (only for transient errors)
        if self.request.retries < self.max_retries and error_category in [
            "api_error",
            "timeout",
        ]:
            raise self.retry(exc=e)

        raise


def _categorize_error(exception: Exception) -> tuple[str, str]:
    """
    Categorize exception and create user-friendly error message.

    Returns:
        (error_category, user_facing_message)
    """
    error_str = str(exception).lower()

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

    async with AsyncSessionLocal() as session:
        # Initialize repositories
        exam_repo = ExamRepository(session)
        topic_repo = TopicRepository(session)
        user_repo = UserRepository(session)

        # Get user and exam
        user = await user_repo.get_by_id(user_id)
        exam = await exam_repo.get_by_id(exam_id)

        if not user or not exam:
            raise ValueError("User or exam not found")

        # Initialize services
        llm = GeminiProvider(
            api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL
        )
        agent = PlanAndExecuteAgent(llm)
        cost_guard = CostGuardService(session)

        agent_service = AgentService(
            agent=agent,
            exam_repo=exam_repo,
            topic_repo=topic_repo,
            cost_guard=cost_guard,
        )

        # Progress callback to update Celery task state
        async def progress_callback(message: str, progress: float):
            task.update_state(
                state="PROGRESS",
                meta={"current": int(progress * 100), "total": 100, "status": message},
            )

        # Generate content
        updated_exam = await agent_service.generate_exam_content(
            user=user, exam_id=exam_id, progress_callback=progress_callback
        )

        await session.commit()

        return {
            "status": "success",
            "exam_id": str(exam_id),
            "topic_count": updated_exam.topic_count,
            "cost_usd": updated_exam.generation_cost_usd,
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
            exam.error_category = error_category
            exam.error_message = error_message
            exam.failed_at = datetime.utcnow()

            await exam_repo.update(exam)
            await session.commit()
