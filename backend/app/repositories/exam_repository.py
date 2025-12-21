from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.exam_mapper import ExamMapper
from app.db.models.exam import ExamModel
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
        from datetime import datetime, timezone
        from app.db.models.topic import TopicModel
        from app.db.models.review import ReviewItemModel
        from app.db.models.study_session import StudySessionModel
        from sqlalchemy import cast, extract, Integer

        # Subquery for completed topics (quiz_completed = True)
        completed_topics_sub = (
            select(func.count(TopicModel.id))
            .where(TopicModel.exam_id == ExamModel.id)
            .where(TopicModel.quiz_completed == True)
            .label("completed_topics")
        )

        # Subquery for due flashcards (next_review_date <= now)
        due_flashcards_sub = (
            select(func.count(ReviewItemModel.id))
            .join(TopicModel, TopicModel.id == ReviewItemModel.topic_id)
            .where(TopicModel.exam_id == ExamModel.id)
            .label("due_flashcards_count")
        )

        # Subquery for actual study time (sum from study_sessions)
        actual_study_time_sub = (
            select(func.sum(
                cast(
                    extract('epoch', StudySessionModel.ended_at - StudySessionModel.started_at) / 60,
                    Integer
                )
            ))
            .where(StudySessionModel.exam_id == ExamModel.id)
            .where(StudySessionModel.ended_at.is_not(None))
            .label("total_actual_study_minutes")
        )

        # Subquery for planned study time
        planned_study_time_sub = (
            select(func.sum(TopicModel.estimated_study_minutes))
            .where(TopicModel.exam_id == ExamModel.id)
            .label("total_planned_study_minutes")
        )
        
        # Subquery for average difficulty level
        avg_difficulty_sub = (
            select(func.avg(TopicModel.difficulty_level))
            .where(TopicModel.exam_id == ExamModel.id)
            .label("average_difficulty")
        )

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
        from datetime import datetime, timezone
        from app.db.models.topic import TopicModel
        from app.db.models.review import ReviewItemModel
        from app.db.models.study_session import StudySessionModel
        from sqlalchemy import cast, extract, Integer

        # Subquery for completed topics
        completed_topics_sub = (
            select(func.count(TopicModel.id))
            .where(TopicModel.exam_id == ExamModel.id)
            .where(TopicModel.quiz_completed == True)
            .label("completed_topics")
        )

        # Subquery for due flashcards
        due_flashcards_sub = (
            select(func.count(ReviewItemModel.id))
            .join(TopicModel, TopicModel.id == ReviewItemModel.topic_id)
            .where(TopicModel.exam_id == ExamModel.id)
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
            .where(StudySessionModel.exam_id == ExamModel.id)
            .where(StudySessionModel.ended_at.is_not(None))
            .label("total_actual_study_minutes")
        )

        # Subquery for planned study time
        planned_study_time_sub = (
            select(func.sum(TopicModel.estimated_study_minutes))
            .where(TopicModel.exam_id == ExamModel.id)
            .label("total_planned_study_minutes")
        )

        # Subquery for average difficulty level
        avg_difficulty_sub = (
            select(func.avg(TopicModel.difficulty_level))
            .where(TopicModel.exam_id == ExamModel.id)
            .label("average_difficulty")
        )

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
        from datetime import datetime, timezone
        from app.db.models.topic import TopicModel
        from app.db.models.review import ReviewItemModel
        from app.db.models.study_session import StudySessionModel
        from sqlalchemy import cast, extract, Integer

        # Subquery for completed topics
        completed_topics_sub = (
            select(func.count(TopicModel.id))
            .where(TopicModel.exam_id == ExamModel.id)
            .where(TopicModel.quiz_completed == True)
            .label("completed_topics")
        )

        # Subquery for due flashcards
        due_flashcards_sub = (
            select(func.count(ReviewItemModel.id))
            .join(TopicModel, TopicModel.id == ReviewItemModel.topic_id)
            .where(TopicModel.exam_id == ExamModel.id)
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
            .where(StudySessionModel.exam_id == ExamModel.id)
            .where(StudySessionModel.ended_at.is_not(None))
            .label("total_actual_study_minutes")
        )

        # Subquery for planned study time
        planned_study_time_sub = (
            select(func.sum(TopicModel.estimated_study_minutes))
            .where(TopicModel.exam_id == ExamModel.id)
            .label("total_planned_study_minutes")
        )

        # Subquery for average difficulty level
        avg_difficulty_sub = (
            select(func.avg(TopicModel.difficulty_level))
            .where(TopicModel.exam_id == ExamModel.id)
            .label("average_difficulty")
        )

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
