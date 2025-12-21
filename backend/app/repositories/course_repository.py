from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import func, select, cast, extract, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.course_mapper import CourseMapper
from app.db.models.course import CourseModel
from app.db.models.exam import ExamModel
from app.db.models.topic import TopicModel
from app.db.models.review import ReviewItemModel
from app.db.models.study_session import StudySessionModel
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
        
        # Subquery for exam count
        exam_count_sub = (
            select(func.count(ExamModel.id))
            .where(ExamModel.course_id == CourseModel.id)
            .label("exam_count")
        )

        # Subquery for total topics
        topic_count_sub = (
            select(func.count(TopicModel.id))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == CourseModel.id)
            .label("topic_count")
        )

        # Subquery for completed topics
        completed_topics_sub = (
            select(func.count(TopicModel.id))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == CourseModel.id)
            .where(TopicModel.quiz_completed == True)
            .label("completed_topics")
        )

        # Subquery for due flashcards
        due_flashcards_sub = (
            select(func.count(ReviewItemModel.id))
            .join(TopicModel, TopicModel.id == ReviewItemModel.topic_id)
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == CourseModel.id)
            .where(ReviewItemModel.next_review_date <= datetime.now(timezone.utc))
            .label("due_flashcards_count")
        )

        # Subquery for actual study time
        actual_study_time_sub = (
            select(func.sum(
                cast(
                    extract('epoch', StudySessionModel.ended_at - StudySessionModel.started_at) / 60,
                    Integer
                )
            ))
            .select_from(StudySessionModel)
            .join(ExamModel, ExamModel.id == StudySessionModel.exam_id)
            .where(ExamModel.course_id == CourseModel.id)
            .where(StudySessionModel.ended_at.is_not(None))
            .label("total_actual_study_minutes")
        )

        # Subquery for planned study time
        planned_study_time_sub = (
            select(func.sum(TopicModel.estimated_study_minutes))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == CourseModel.id)
            .label("total_planned_study_minutes")
        )

        # Subquery for average difficulty level
        avg_difficulty_sub = (
            select(func.avg(TopicModel.difficulty_level))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == CourseModel.id)
            .label("average_difficulty")
        )

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
        
        # Subquery for exam count
        exam_count_sub = (
            select(func.count(ExamModel.id))
            .where(ExamModel.course_id == course_id)
            .label("exam_count")
        )

        # Similar subqueries as in list_by_user but filtered by course_id directly
        topic_count_sub = (
            select(func.count(TopicModel.id))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == course_id)
            .label("topic_count")
        )

        completed_topics_sub = (
            select(func.count(TopicModel.id))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == course_id)
            .where(TopicModel.quiz_completed == True)
            .label("completed_topics")
        )

        due_flashcards_sub = (
            select(func.count(ReviewItemModel.id))
            .join(TopicModel, TopicModel.id == ReviewItemModel.topic_id)
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == course_id)
            .where(ReviewItemModel.next_review_date <= datetime.now(timezone.utc))
            .label("due_flashcards_count")
        )

        actual_study_time_sub = (
            select(func.sum(
                cast(
                    extract('epoch', StudySessionModel.ended_at - StudySessionModel.started_at) / 60,
                    Integer
                )
            ))
            .select_from(StudySessionModel)
            .join(ExamModel, ExamModel.id == StudySessionModel.exam_id)
            .where(ExamModel.course_id == course_id)
            .where(StudySessionModel.ended_at.is_not(None))
            .label("total_actual_study_minutes")
        )

        planned_study_time_sub = (
            select(func.sum(TopicModel.estimated_study_minutes))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == course_id)
            .label("total_planned_study_minutes")
        )

        avg_difficulty_sub = (
            select(func.avg(TopicModel.difficulty_level))
            .join(ExamModel, ExamModel.id == TopicModel.exam_id)
            .where(ExamModel.course_id == course_id)
            .label("average_difficulty")
        )

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
