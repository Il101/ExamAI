from typing import List, Optional, Tuple
from uuid import UUID

from app.domain.exam import Exam, ExamStatus
from app.domain.user import User
from app.integrations.llm.base import LLMProvider
from app.repositories.exam_repository import ExamRepository
from celery import chain

from app.services.cost_guard_service import CostGuardService
from app.tasks.exam_tasks import create_exam_plan, generate_exam_content


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
        exam_type: str,
        level: str,
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
        cleaned_length = len(cleaned_content.strip())
        if cleaned_length < 100:
            raise ValueError(
                f"Content must be at least 100 characters after cleaning. "
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

        # Cannot delete during generation
        if exam.status == "generating":
            raise ValueError("Cannot delete exam during generation")

        return await self.exam_repo.delete(exam_id)

    async def start_generation(self, user_id: UUID, exam_id: UUID) -> Tuple[Exam, str]:
        """
        Start exam generation process.
        This marks exam as "generating" and triggers a chain of background tasks:
        1. Create exam plan (topics)
        2. Generate content for each topic

        Returns:
            Tuple of (Updated exam, Task ID of the first task in the chain)
        """
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")

        # Check if can generate
        # This should be checked for the initial state (e.g., 'draft' or 'planned')
        if not exam.can_generate():
            raise ValueError(f"Cannot generate exam with status: {exam.status}")

        exam.start_generation()
        updated = await self.exam_repo.update(exam)

        # Create a Celery chain: plan -> generate
        # The `generate_exam_content` task will be triggered after `create_exam_plan` succeeds.
        # Note: We need to ensure the signature of the tasks is compatible with chaining,
        # or that the second task can get its required arguments.
        # `generate_exam_content` takes exam_id and user_id, which we have.
        # We can create a chain where the result of the first task is ignored,
        # and the second task is called with its own arguments by using an immutable signature (.si).
        generation_chain = chain(
            create_exam_plan.s(exam_id=str(exam_id), user_id=str(user_id)),
            generate_exam_content.si(exam_id=str(exam_id), user_id=str(user_id)),
        )

        task = generation_chain.apply_async()

        return updated, task.id

    async def create_plan(
        self, user_id: UUID, exam_id: UUID
    ) -> Tuple[Exam, str]:
        """
        Create topic plan without generating content (progressive generation step 1).
        
        Returns:
            Tuple of (Updated exam, Task ID)
        """
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
        
        # Check if can create plan
        if not exam.can_create_plan():
            raise ValueError(f"Cannot create plan: status={exam.status}")
        
        # Mark as generating (will become 'planned' after task completes)
        exam.start_generation()
        updated = await self.exam_repo.update(exam)
        
        # Trigger background task to create plan
        task = create_exam_plan.delay(
            exam_id=str(exam_id), user_id=str(user_id)
        )
        
        return updated, task.id
