from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from app.domain.exam import Exam, ExamStatus, ExamType, ExamLevel
from app.domain.user import User
from app.integrations.llm.base import LLMProvider
from app.repositories.exam_repository import ExamRepository
from celery import chain

from app.services.cost_guard_service import CostGuardService
# Task imports moved to function level to avoid circular import


class ExamService:
    """
    Service for exam management.
    Handles exam creation, generation, retrieval.
    """

    def __init__(
        self,
        exam_repo: ExamRepository,
        cost_guard: CostGuardService,
        llm_provider: LLMProvider,
    ):
        self.exam_repo = exam_repo
        self.cost_guard = cost_guard
        self.llm = llm_provider

    async def create_exam(
        self,
        user: User,
        title: str,
        subject: str,
        exam_type: ExamType,
        level: ExamLevel,
        original_content: str,
        exam_date: Optional[datetime] = None,
    ) -> Exam:
        """
        Create new exam.

        Args:
            user: User creating exam
            title: Exam title
            subject: Subject name
            exam_type: Type (oral, written, test)
            level: Level (school, bachelor, master, phd)
            original_content: Study material content

        Returns:
            Created exam

        Raises:
            ValueError: If validation fails or limits exceeded
        """
        # Check concurrent exam limit (unlimited if None)
        exam_count = await self.exam_repo.count_by_user(user.id, status="ready")
        max_exams = user.get_max_exam_count()

        if max_exams is not None and exam_count >= max_exams:
            raise ValueError(
                f"Concurrent exam limit reached ({max_exams} for {user.subscription_plan} plan). "
                "Please delete old exams to create new ones."
            )

        # Check daily creation limit
        from app.core.rate_limiter import exam_creation_tracker
        from app.core.limits_config import PLAN_LIMITS
        
        daily_limit = PLAN_LIMITS.get(user.subscription_plan, PLAN_LIMITS["free"]).get("daily_exam_creations")
        if daily_limit is not None:
            current_daily = await exam_creation_tracker.get_count(str(user.id))
            if current_daily >= daily_limit:
                raise ValueError(
                    f"Daily exam creation limit reached ({daily_limit} per day). "
                    "Please try again tomorrow."
                )

        # Clean content: remove null bytes and other invalid UTF-8 characters
        # PostgreSQL TEXT doesn't allow null bytes (0x00)
        # Also handle cases where PDF extraction might produce binary data
        try:
            # Remove null bytes
            cleaned_content = original_content.replace('\x00', '')
            # Remove other control characters except newlines and tabs
            cleaned_content = ''.join(
                char for char in cleaned_content 
                if ord(char) >= 32 or char in '\n\t\r'
            )
            # Ensure valid UTF-8 encoding
            cleaned_content = cleaned_content.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to clean content: {str(e)}")
        
        # Validate cleaned content length
        # NOTE: Skip validation if original_content is empty (file upload path)
        # For file uploads, content is in Gemini Files API, not in original_content
        if original_content:  # Only validate if content provided
            cleaned_length = len(cleaned_content.strip())
            if cleaned_length < 50:
                raise ValueError(
                    f"Content must be at least 50 characters after cleaning. "
                    f"Got {cleaned_length} characters. "
                    f"Original length: {len(original_content)}"
                )

        # Estimate cost
        estimated_tokens = len(cleaned_content) // 4
        estimated_cost = self.llm.calculate_cost(estimated_tokens, estimated_tokens * 2)

        # Check budget
        budget_check = await self.cost_guard.check_budget(user, estimated_cost)
        if not budget_check["allowed"]:
            remaining = await self.cost_guard.get_remaining_budget(user)
            raise ValueError(f"Insufficient budget. Remaining: ${remaining:.2f}")

        # Create exam
        exam = Exam(
            user_id=user.id,
            title=title,
            subject=subject,
            exam_type=exam_type,
            level=level,
            original_content=cleaned_content,
            exam_date=exam_date,
            status="draft",
        )

        created = await self.exam_repo.create(exam)

        # Track usage
        from app.core.rate_limiter import exam_creation_tracker
        await exam_creation_tracker.increment(str(user.id))

        return created

    async def get_exam(self, user_id: UUID, exam_id: UUID) -> Optional[Exam]:
        """
        Get exam by ID (with authorization check).

        Returns:
            Exam if found and owned by user, None otherwise
        """
        return await self.exam_repo.get_by_user_and_id(user_id, exam_id)

    async def list_user_exams(
        self,
        user_id: UUID,
        status: Optional[ExamStatus] = None,
        course_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Exam]:
        """List user's exams"""
        return await self.exam_repo.list_by_user(
            user_id=user_id, status=status, course_id=course_id, limit=limit, offset=offset
        )

    async def update_exam(
        self, user_id: UUID, exam_id: UUID, updates: dict
    ) -> Optional[Exam]:
        """
        Update exam (with authorization check).

        Args:
            user_id: User ID
            exam_id: Exam ID
            updates: Dictionary with fields to update

        Returns:
            Updated exam if found and owned by user, None otherwise
        """
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            return None

        # Cannot update during generation
        if exam.status == "generating":
            raise ValueError("Cannot update exam during generation")

        # Apply updates
        for key, value in updates.items():
            if hasattr(exam, key):
                setattr(exam, key, value)

        # Validate
        exam._validate()

        updated = await self.exam_repo.update(exam)

        # If exam_date changed, trigger rescheduling of topics
        if "exam_date" in updates and updates["exam_date"]:
            try:
                from app.repositories.topic_repository import TopicRepository
                from app.services.study_planner_service import StudyPlannerService
                
                topic_repo = TopicRepository(self.exam_repo.session)
                topics = await topic_repo.get_by_exam_id(exam_id)
                
                if topics:
                    planner = StudyPlannerService()
                    updated_topics = planner.schedule_exam(updated, topics)
                    for topic in updated_topics:
                        await topic_repo.update(topic)
                    await self.exam_repo.session.flush()
            except Exception as e:
                # Log but don't fail the primary update
                import logging
                logging.getLogger(__name__).error(f"FAILED TO RESCHEDULE TOPICS after date update: {e}")

        return updated

    async def delete_exam(self, user_id: UUID, exam_id: UUID) -> bool:
        """
        Delete exam (with authorization check).

        Returns:
            True if deleted, False if not found
        """
        # Check ownership
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            return False

        # Allow deletion even during generation to handle stuck jobs
        # if exam.status == "generating":
        #     raise ValueError("Cannot delete exam during generation")

        return await self.exam_repo.delete(exam_id)

    async def start_generation(
        self, user_id: UUID, exam_id: UUID
    ) -> Tuple[Exam, str]:
        """
        Start content generation for exam.
        Exam must be in 'planned' status (topics already created).
        
        Returns:
            Tuple of (Updated exam, Task ID)
        """
        from app.tasks.exam_tasks import generate_exam_content
        
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")

        # Check if can generate (requires 'planned' status and topics)
        if not exam.can_generate():
            raise ValueError(f"Cannot generate exam with status: {exam.status}, topic_count: {exam.topic_count}")

        # Mark as generating
        exam.start_generation()
        updated = await self.exam_repo.update(exam)

        # Start content generation task
        task = generate_exam_content.apply_async(args=[str(exam_id), str(user_id)])

        return updated, task.id
