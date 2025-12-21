from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.course_mapper import CourseMapper
from app.db.models.course import CourseModel
from app.db.models.exam import ExamModel
from app.repositories.utils.stats_utils import get_course_stats_subqueries
from app.domain.course import Course
from app.repositories.base import BaseRepository

class CourseRepository(BaseRepository[Course, CourseModel]):
    """Repository for Course entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CourseModel, CourseMapper)

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Course]:
        """List courses by user with aggregated statistics"""
        
        # Get shared subqueries
        (
            exam_count_sub,
            topic_count_sub,
            completed_topics_sub,
            due_flashcards_sub,
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub
        ) = get_course_stats_subqueries()

        stmt = select(
            CourseModel,
            exam_count_sub,
            topic_count_sub,
            completed_topics_sub,
            due_flashcards_sub,
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub
        ).where(CourseModel.user_id == user_id)

        stmt = stmt.order_by(CourseModel.created_at.desc()).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        rows = result.all()

        courses = []
        for (
            model, 
            exam_count, 
            topic_count, 
            completed_count, 
            due_count, 
            actual_minutes, 
            planned_minutes, 
            avg_diff
        ) in rows:
            setattr(model, "exam_count", exam_count or 0)
            setattr(model, "topic_count", topic_count or 0)
            setattr(model, "completed_topics", completed_count or 0)
            setattr(model, "due_flashcards_count", due_count or 0)
            setattr(model, "total_actual_study_minutes", actual_minutes or 0)
            setattr(model, "total_planned_study_minutes", planned_minutes or 0)
            setattr(model, "average_difficulty", float(avg_diff or 0.0))
            courses.append(self.mapper.to_domain(model))

        return courses

    async def count_by_user(self, user_id: UUID) -> int:
        """Count user's courses"""
        stmt = (
            select(func.count())
            .select_from(CourseModel)
            .where(CourseModel.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_user_and_id(self, user_id: UUID, course_id: UUID) -> Optional[Course]:
        """Get course by user and ID with aggregated statistics"""
        
        # Get shared subqueries (the helpers already use the models correctly with correlations)
        (
            exam_count_sub,
            topic_count_sub,
            completed_topics_sub,
            due_flashcards_sub,
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub
        ) = get_course_stats_subqueries()

        stmt = select(
            CourseModel,
            exam_count_sub,
            topic_count_sub,
            completed_topics_sub,
            due_flashcards_sub,
            actual_study_time_sub,
            planned_study_time_sub,
            avg_difficulty_sub
        ).where(CourseModel.id == course_id, CourseModel.user_id == user_id)

        result = await self.session.execute(stmt)
        row = result.first()

        if row is None:
            return None

        (
            model, 
            exam_count, 
            topic_count, 
            completed_count, 
            due_count, 
            actual_minutes, 
            planned_minutes, 
            avg_diff
        ) = row
        
        setattr(model, "exam_count", exam_count or 0)
        setattr(model, "topic_count", topic_count or 0)
        setattr(model, "completed_topics", completed_count or 0)
        setattr(model, "due_flashcards_count", due_count or 0)
        setattr(model, "total_actual_study_minutes", actual_minutes or 0)
        setattr(model, "total_planned_study_minutes", planned_minutes or 0)
        setattr(model, "average_difficulty", float(avg_diff or 0.0))
        
        return self.mapper.to_domain(model)
