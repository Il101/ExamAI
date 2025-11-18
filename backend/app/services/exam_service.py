from typing import List, Optional
from uuid import UUID
from app.domain.exam import Exam, ExamStatus
from app.domain.user import User
from app.repositories.exam_repository import ExamRepository
from app.services.cost_guard_service import CostGuardService
from app.integrations.llm.base import LLMProvider


class ExamService:
    """
    Service for exam management.
    Handles exam creation, generation, retrieval.
    """
    
    def __init__(
        self,
        exam_repo: ExamRepository,
        cost_guard: CostGuardService,
        llm_provider: LLMProvider
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
        original_content: str
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
            raise ValueError(f"Exam limit reached ({max_exams} for {user.subscription_plan} plan)")
        
        # Estimate cost
        estimated_tokens = len(original_content) // 4
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
            original_content=original_content,
            status="draft"
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
        offset: int = 0
    ) -> List[Exam]:
        """List user's exams"""
        return await self.exam_repo.list_by_user(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
    
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
    
    async def start_generation(self, user_id: UUID, exam_id: UUID) -> Exam:
        """
        Start exam generation process.
        This marks exam as "generating" and triggers background task.
        
        Returns:
            Updated exam
        """
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
            
        if exam.status == "generating":
            return exam
            
        exam.status = "generating"
        updated = await self.exam_repo.update(exam)
        
        # TODO: Trigger background task (Celery/Arq)
        
        return updated
