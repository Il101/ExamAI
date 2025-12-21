from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.exam_mapper import ExamMapper
from app.db.models.exam import ExamModel
from app.repositories.utils.stats_utils import get_exam_stats_subqueries
from app.domain.exam import Exam, ExamStatus
from app.repositories.base import BaseRepository


class ExamRepository(BaseRepository[Exam, ExamModel]):
    """Repository for Exam entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ExamModel, ExamMapper)

    async def list_by_user(
        self,
        user_id: UUID,
        status: Optional[ExamStatus] = None,
        course_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Exam]:
        """List exams by user with optional status filter and progress counts"""
        # Get shared subqueries
        (
            completed_topics_sub,
            due_flashcards_sub,
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub
        ) = get_exam_stats_subqueries()

        from app.db.models.course import CourseModel

        stmt = select(
            ExamModel, 
            completed_topics_sub, 
            due_flashcards_sub, 
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub,
            CourseModel.title.label("course_title")
        ).outerjoin(CourseModel, CourseModel.id == ExamModel.course_id).where(ExamModel.user_id == user_id)

        if status:
            stmt = stmt.where(ExamModel.status == status)
            
        if course_id:
            stmt = stmt.where(ExamModel.course_id == course_id)
        elif course_id is False: # Special case for "standalone" (no course)
             stmt = stmt.where(ExamModel.course_id == None)

        stmt = stmt.order_by(ExamModel.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        rows = result.all()

        exams = []
        for model, completed_count, due_count, actual_minutes, planned_minutes, avg_diff, course_title in rows:
            setattr(model, "completed_topics", completed_count)
            setattr(model, "due_flashcards_count", due_count)
            setattr(model, "total_actual_study_minutes", actual_minutes or 0)
            setattr(model, "total_planned_study_minutes", planned_minutes or 0)
            setattr(model, "average_difficulty", float(avg_diff or 0.0))
            setattr(model, "course_title", course_title)
            exams.append(self.mapper.to_domain(model))

        return exams

    async def list_by_course(
        self,
        user_id: UUID,
        course_id: UUID,
    ) -> List[Exam]:
        """List all exams belonging to a specific course"""
        # Get shared subqueries
        (
            completed_topics_sub,
            due_flashcards_sub,
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub
        ) = get_exam_stats_subqueries()

        from app.db.models.course import CourseModel

        stmt = select(
            ExamModel, 
            completed_topics_sub, 
            due_flashcards_sub, 
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub,
            CourseModel.title.label("course_title")
        ).outerjoin(CourseModel, CourseModel.id == ExamModel.course_id).where(
            ExamModel.user_id == user_id,
            ExamModel.course_id == course_id
        ).order_by(ExamModel.created_at.desc())

        result = await self.session.execute(stmt)
        rows = result.all()

        exams = []
        for model, completed_count, due_count, actual_minutes, planned_minutes, avg_diff, course_title in rows:
            setattr(model, "completed_topics", completed_count or 0)
            setattr(model, "due_flashcards_count", due_count or 0)
            setattr(model, "total_actual_study_minutes", actual_minutes or 0)
            setattr(model, "total_planned_study_minutes", planned_minutes or 0)
            setattr(model, "average_difficulty", float(avg_diff or 0.0))
            setattr(model, "course_title", course_title)
            exams.append(self.mapper.to_domain(model))

        return exams

    async def count_by_user(
        self, 
        user_id: UUID, 
        status: Optional[ExamStatus] = None,
        course_id: Optional[UUID] = None
    ) -> int:
        """Count user's exams"""
        stmt = (
            select(func.count())
            .select_from(ExamModel)
            .where(ExamModel.user_id == user_id)
        )

        if status:
            stmt = stmt.where(ExamModel.status == status)

        if course_id:
            stmt = stmt.where(ExamModel.course_id == course_id)
        elif course_id is False:
            stmt = stmt.where(ExamModel.course_id == None)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_user_and_id(self, user_id: UUID, exam_id: UUID) -> Optional[Exam]:
        """Get exam by user and ID with progress counts"""
        # Get shared subqueries
        (
            completed_topics_sub,
            due_flashcards_sub,
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub
        ) = get_exam_stats_subqueries()

        from app.db.models.course import CourseModel

        stmt = select(
            ExamModel, 
            completed_topics_sub, 
            due_flashcards_sub, 
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub,
            CourseModel.title.label("course_title")
        ).outerjoin(CourseModel, CourseModel.id == ExamModel.course_id).where(
            ExamModel.id == exam_id, ExamModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        row = result.first()

        if row is None:
            return None

        model, completed_count, due_count, actual_minutes, planned_minutes, avg_diff, course_title = row
        setattr(model, "completed_topics", completed_count)
        setattr(model, "due_flashcards_count", due_count)
        setattr(model, "total_actual_study_minutes", actual_minutes or 0)
        setattr(model, "total_planned_study_minutes", planned_minutes or 0)
        setattr(model, "average_difficulty", float(avg_diff or 0.0))
        setattr(model, "course_title", course_title)
        
        return self.mapper.to_domain(model)
