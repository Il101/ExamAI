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
        # Check exam count limit
        exam_count = await self.exam_repo.count_by_user(user.id, status="ready")
        max_exams = user.get_max_exam_count()

        if exam_count >= max_exams:
            raise ValueError(
                f"Exam limit reached ({max_exams} for {user.subscription_plan} plan)"
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
            status="draft",
        )

        created = await self.exam_repo.create(exam)

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
        limit: int = 100,
        offset: int = 0,
    ) -> List[Exam]:
        """List user's exams"""
        return await self.exam_repo.list_by_user(
            user_id=user_id, status=status, limit=limit, offset=offset
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

        return await self.exam_repo.update(exam)

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
        Start content generation for exam (progressive generation step 2).
        Exam must be in 'planned' status (topics already created).
        
        Returns:
            Tuple of (Updated exam, Task ID)
        """
        # Import tasks here to avoid circular import
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

    async def create_plan(
        self, user_id: UUID, exam_id: UUID
    ) -> Tuple[Exam, str]:
        """
        Create topic plan without generating content (progressive generation step 1).
        
        Returns:
            Tuple of (Updated exam, Task ID)
        """
        # Import tasks here to avoid circular import
        from app.tasks.exam_tasks import create_exam_plan
        
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
        
        # Check if can create plan
        if not exam.can_create_plan():
            raise ValueError(f"Cannot create plan: status={exam.status}")
        
        # Mark as planning (task will mark as 'planned' when complete)
        exam.start_planning()
        updated = await self.exam_repo.update(exam)
        
        # Start plan creation task
        task = create_exam_plan.apply_async(args=[str(exam_id), str(user_id)])
        
        return updated, task.id
