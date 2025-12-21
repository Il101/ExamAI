from datetime import date
from typing import List, Optional
from uuid import UUID

from app.domain.course import Course
from app.domain.exam import Exam
from app.domain.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.exam_repository import ExamRepository

class CourseService:
    """
    Service for Course management.
    Handles course lifecycle and exam grouping.
    """

    def __init__(
        self,
        course_repo: CourseRepository,
        exam_repo: ExamRepository,
    ):
        self.course_repo = course_repo
        self.exam_repo = exam_repo

    async def create_course(
        self,
        user: User,
        title: str,
        subject: str,
        description: Optional[str] = None,
        semester_start: Optional[date] = None,
        semester_end: Optional[date] = None,
    ) -> Course:
        """Create a new course/folder"""
        from app.core.limits_config import PLAN_LIMITS
        
        # Check course limit
        course_count = await self.course_repo.count_by_user(user.id)
        max_courses = PLAN_LIMITS.get(user.subscription_plan, PLAN_LIMITS["free"]).get("max_courses", 2)
        
        if max_courses is not None and course_count >= max_courses:
            raise ValueError(
                f"Course limit reached ({max_courses} for {user.subscription_plan} plan). "
                "Please delete old courses to create new ones."
            )

        course = Course(
            user_id=user.id,
            title=title,
            subject=subject,
            description=description,
            semester_start=semester_start,
            semester_end=semester_end,
        )
        
        return await self.course_repo.create(course)

    async def get_course(self, user_id: UUID, course_id: UUID) -> Optional[Course]:
        """Get course by ID with aggregated stats"""
        return await self.course_repo.get_by_user_and_id(user_id, course_id)

    async def list_user_courses(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Course]:
        """List user's courses with aggregated stats"""
        return await self.course_repo.list_by_user(user_id, limit, offset)

    async def update_course(
        self, user_id: UUID, course_id: UUID, updates: dict
    ) -> Optional[Course]:
        """Update course metadata"""
        course = await self.course_repo.get_by_user_and_id(user_id, course_id)
        if not course:
            return None

        for key, value in updates.items():
            if hasattr(course, key):
                setattr(course, key, value)

        course._validate()
        return await self.course_repo.update(course)

    async def delete_course(self, user_id: UUID, course_id: UUID) -> bool:
        """Delete course. Exams will NOT be deleted, but moved to standalone."""
        course = await self.course_repo.get_by_user_and_id(user_id, course_id)
        if not course:
            return False
            
        # We don't need to manually update exams if we set ondelete="SET NULL" in DB,
        # but let's be explicit if we want to ensure or if we want to delete exams too.
        # User said "folders", usually deleting a folder might delete contents or not.
        # Implementation Plan says "Exams will NOT be deleted".
        return await self.course_repo.delete(course_id)

    async def add_exam_to_course(self, user_id: UUID, course_id: UUID, exam_id: UUID) -> bool:
        """Add an existing exam to a course"""
        course = await self.course_repo.get_by_user_and_id(user_id, course_id)
        if not course:
            raise ValueError("Course not found")
            
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
            
        exam.course_id = course_id
        await self.exam_repo.update(exam)
        return True

    async def remove_exam_from_course(self, user_id: UUID, exam_id: UUID) -> bool:
        """Remove exam from its course (move to standalone)"""
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
            
        exam.course_id = None
        await self.exam_repo.update(exam)
        return True

    async def get_course_exams(self, user_id: UUID, course_id: UUID) -> List[Exam]:
        """List all exams in a course"""
        return await self.exam_repo.list_by_course(user_id, course_id)
