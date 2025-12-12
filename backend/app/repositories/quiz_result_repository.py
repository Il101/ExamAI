from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.quiz_result_mapper import QuizResultMapper
from app.db.models.quiz_result import QuizResultModel
from app.domain.quiz_result import QuizResult
from app.repositories.base import BaseRepository


class QuizResultRepository(BaseRepository[QuizResult, QuizResultModel]):
    """Repository for QuizResult entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, QuizResultModel, QuizResultMapper)

    async def create_result(
        self,
        user_id: UUID,
        topic_id: UUID,
        questions_total: int,
        questions_correct: int,
    ) -> QuizResult:
        """Create a new quiz result"""
        from uuid import uuid4

        model = QuizResultModel(
            id=uuid4(),
            user_id=user_id,
            topic_id=topic_id,
            questions_total=questions_total,
            questions_correct=questions_correct,
        )

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return QuizResultMapper.to_domain(model)

    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get aggregate quiz statistics for a user.
        
        Returns:
            {
                "total_quizzes": int,
                "questions_correct": int,
                "questions_total": int,
                "average_score": float
            }
        """
        stmt = select(
            func.count(QuizResultModel.id).label("total_quizzes"),
            func.sum(QuizResultModel.questions_correct).label("questions_correct"),
            func.sum(QuizResultModel.questions_total).label("questions_total"),
        ).where(QuizResultModel.user_id == user_id)

        result = await self.session.execute(stmt)
        row = result.one()

        total_quizzes = row.total_quizzes or 0
        questions_correct = row.questions_correct or 0
        questions_total = row.questions_total or 0

        average_score = (
            (questions_correct / questions_total * 100) if questions_total > 0 else 0.0
        )

        return {
            "total_quizzes": total_quizzes,
            "questions_correct": questions_correct,
            "questions_total": questions_total,
            "average_score": round(average_score, 1),
        }

    async def get_recent_results(
        self, user_id: UUID, limit: int = 10
    ) -> list[QuizResult]:
        """Get recent quiz results for a user"""
        stmt = (
            select(QuizResultModel)
            .where(QuizResultModel.user_id == user_id)
            .order_by(QuizResultModel.completed_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [QuizResultMapper.to_domain(model) for model in models]

    async def get_topic_results(self, topic_id: UUID) -> list[QuizResult]:
        """Get all quiz results for a specific topic"""
        stmt = (
            select(QuizResultModel)
            .where(QuizResultModel.topic_id == topic_id)
            .order_by(QuizResultModel.completed_at.desc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [QuizResultMapper.to_domain(model) for model in models]

    async def get_daily_activity(self, user_id: UUID, days: int = 7) -> list[Dict[str, Any]]:
        """
        Get daily quiz activity for a user.
        
        Returns list of dicts: [{"date": date, "quizzes_completed": int, "questions_correct": int}]
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                func.date(QuizResultModel.completed_at).label("quiz_date"),
                func.count(QuizResultModel.id).label("quizzes_completed"),
                func.sum(QuizResultModel.questions_correct).label("questions_correct"),
            )
            .where(
                QuizResultModel.user_id == user_id,
                QuizResultModel.completed_at >= start_date,
            )
            .group_by("quiz_date")
            .order_by("quiz_date")
        )

        result = await self.session.execute(stmt)

        activity = []
        for row in result:
            activity.append({
                "date": row.quiz_date,
                "quizzes_completed": row.quizzes_completed,
                "questions_correct": row.questions_correct or 0,
            })

        return activity
