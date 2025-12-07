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
from app.tasks.celery_app import celery_app


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

    This is the EXECUTION phase of progressive generation.
    It assumes the exam is already PLANNED (has topics).
    1. Gets exam and topics from database
    2. Generates content for each pending topic
    3. Finalizes the exam
    """

    print(f"[CELERY] Starting generate_exam_content task for exam_id={exam_id}, user_id={user_id}")
    print(f"[CELERY] Task ID: {self.request.id}")
    
    try:
        print(f"[CELERY] Running async generation...")
        # Run async code in sync Celery task
        result = asyncio.run(
            _generate_exam_content_async(
                exam_id=UUID(exam_id), user_id=UUID(user_id), task=self
            )
        )
        
        print(f"[CELERY] Generation completed successfully for exam {exam_id}")
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
    print(f"[CELERY ASYNC] Starting async generation for exam {exam_id}")
    
    async with AsyncSessionLocal() as session:
        print(f"[CELERY ASYNC] Session created, initializing repositories...")
        # Initialize repositories
        exam_repo = ExamRepository(session)
        topic_repo = TopicRepository(session)
        user_repo = UserRepository(session)
        review_repo = ReviewItemRepository(session)

        print(f"[CELERY ASYNC] Fetching user and exam from database...")
        # Get user and exam
        user = await user_repo.get_by_id(user_id)
        exam = await exam_repo.get_by_id(exam_id)

        if not user or not exam:
            raise ValueError("User or exam not found")

        print(f"[CELERY ASYNC] User and exam found. Initializing AI services...")
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
            review_repo=review_repo,
            cost_guard=cost_guard,
        )

        # Progress callback to update Celery task state
        async def progress_callback(message: str, progress: float):
            task.update_state(
                state="PROGRESS",
                meta={"current": int(progress * 100), "total": 100, "status": message},
            )

        print(f"[CELERY ASYNC] Starting agent_service.generate_exam_content...")
        # Generate content (Execute phase)
        # We need to adapt agent_service.generate_exam_content to support
        # resuming from PLANNED state or just use the executor directly.
        # For now, let's assume agent_service handles the logic of checking state.
        updated_exam = await agent_service.generate_exam_content(
            user=user, exam_id=exam_id, progress_callback=progress_callback
        )
        print(f"[CELERY ASYNC] Agent service completed successfully!")

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
# Progressive generation tasks - append to exam_tasks.py

@celery_app.task(
    bind=True,
    name="create_exam_plan",
    base=ExamGenerationTask,
    max_retries=3,
    default_retry_delay=60,
)
def create_exam_plan(self, exam_id: str, user_id: str):
    """Create topic plan for exam without generating content (progressive generation step 1)"""
    try:
        result = asyncio.run(
            _create_exam_plan_async(
                exam_id=UUID(exam_id),
                user_id=UUID(user_id),
            )
        )
        return {"status": "success", "topic_count": result}
    except Exception as e:
        error_category, user_message = _categorize_error(e)
        asyncio.run(_mark_exam_failed(UUID(exam_id), error_category, user_message))
        
        if self.request.retries < self.max_retries and error_category in ["api_error", "timeout"]:
            raise self.retry(exc=e)
        raise


async def _create_exam_plan_async(exam_id: UUID, user_id: UUID) -> int:
    """Async implementation of plan creation"""
    async with AsyncSessionLocal() as session:
        exam_repo = ExamRepository(session)
        topic_repo = TopicRepository(session)
        user_repo = UserRepository(session)
        
        exam = await exam_repo.get_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")
        
        # Verify exam is in correct status
        if exam.status != "planning":
            raise ValueError(f"Exam must be in 'planning' status, got: {exam.status}")
        
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        llm_provider = get_llm_provider()
        cost_guard = CostGuardService(session)
        
        estimated_cost = llm_provider.calculate_cost(5000, 5000)
        budget_check = await cost_guard.check_budget(user, estimated_cost)
        if not budget_check["allowed"]:
            raise ValueError("Insufficient budget for plan creation")
        
        from app.agent.planner import CoursePlanner
        from app.agent.state import AgentState
        
        state = AgentState(
            user_request=f"Generate exam content for {exam.subject}",
            subject=exam.subject,
            level=exam.level,
            exam_type=exam.exam_type,
            original_content=exam.original_content,
        )
        
        planner = CoursePlanner(llm_provider)
        plan_steps = await planner.make_plan(state)
        
        topics = []
        for idx, step in enumerate(plan_steps):
            topic = Topic(
                exam_id=exam_id,
                user_id=user_id,
                topic_name=step.title,
                content="",
                status="pending",
                order_index=idx,
                generation_priority=step.priority.value,
                difficulty_level=3,
            )
            topics.append(topic)
        
        created_topics = await topic_repo.bulk_create(topics)
        
        exam.mark_as_planned()
        exam.update_topic_count(len(created_topics))
        await exam_repo.update(exam)
        
        await cost_guard.log_usage(
            user_id=user.id,
            model_name=settings.GEMINI_MODEL,
            provider="gemini",
            operation_type="plan_creation",
            input_tokens=state.total_tokens_used // 2,
            output_tokens=state.total_tokens_used // 2,
            cost_usd=state.total_cost_usd,
        )
        
        await session.commit()
        return len(created_topics)


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
        
        llm_provider = get_llm_provider()
        cost_guard = CostGuardService(session)
        
        from app.agent.executor import TopicExecutor
        from app.agent.state import AgentState, PlanStep
        from app.domain.priority import Priority
        
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
            description="",
            priority=Priority(topic.generation_priority) if topic.generation_priority in [1,2,3] else Priority.MEDIUM,
            estimated_paragraphs=5,
            dependencies=[],
        )
        
        executor = TopicExecutor(llm_provider)
        step_result = await executor.execute_step(state, plan_step, {})
        
        if not step_result.success:
            raise ValueError(f"Failed to generate topic: {step_result.error_message}")
        
        topic.mark_as_ready(step_result.content)
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

@celery_app.task(
    bind=True,
    name="extract_exam_content",
    base=ExamGenerationTask,
    max_retries=3,
    default_retry_delay=60,
)
def extract_exam_content(self, exam_id: str):
    """
    Background task to extract text from exam source file and update DB.
    This replaces the 'placeholder' content set during creation.
    """
    try:
        asyncio.run(_extract_exam_content_async(UUID(exam_id)))
        return {"status": "success", "exam_id": exam_id}
    except Exception as e:
        print(f"Extraction task failed for exam {exam_id}: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        raise

async def _extract_exam_content_async(exam_id: UUID):
    """Async implementation of content extraction"""
    async with AsyncSessionLocal() as session:
        exam_repo = ExamRepository(session)
        exam = await exam_repo.get_by_id(exam_id)
        
        if not exam or not exam.original_file_url:
            print(f"Exam {exam_id} not found or has no file URL")
            return
            
        # Download file from storage
        from app.dependencies import get_storage
        storage = get_storage()
        
        try:
            # Check if content is already real (not placeholder)
            if exam.original_content and len(exam.original_content) > 200 and "Content processed directly" not in exam.original_content:
                return # Already extracted
            
            print(f"Starting background extraction for exam {exam_id}...")
            file_data = await storage.download_file(exam.original_file_url)
            
            # Extract text
            from app.utils.extraction import extract_text_generic
            mime_type = exam.original_file_mime_type or "application/pdf"
            extracted_text = extract_text_generic(file_data, mime_type)
            
            if extracted_text and len(extracted_text) > 100:
                # Update DB
                exam.original_content = extracted_text
                await exam_repo.update(exam)
                
                # Upload text to storage (for cache recovery compatibility)
                text_path = f"exams/{exam.id}/original_content.txt"
                await storage.upload_file(extracted_text.encode('utf-8'), text_path)
                
                await session.commit()
                print(f"Successfully extracted and updated content for exam {exam.id} ({len(extracted_text)} chars)")
            else:
                print(f"Extraction yielded too little text for exam {exam_id}")
                
        except Exception as e:
            print(f"Failed to process file for exam {exam_id}: {e}")
            raise
