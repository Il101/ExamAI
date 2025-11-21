from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.study_session_mapper import StudySessionMapper
from app.db.models.study_session import StudySessionModel
from app.domain.study_session import StudySession
from app.repositories.base import BaseRepository


class StudySessionRepository(BaseRepository[StudySession, StudySessionModel]):
    """Repository for StudySession entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, StudySessionModel, StudySessionMapper)

    async def get_active_by_user(self, user_id: UUID) -> Optional[StudySession]:
        """Get active study session for user"""
        stmt = select(StudySessionModel).where(
            StudySessionModel.user_id == user_id,
            StudySessionModel.is_active.is_(True),
        )

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self.mapper.to_domain(model)

    async def list_by_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[StudySession]:
        """List study sessions by user"""
        stmt = (
            select(StudySessionModel)
            .where(StudySessionModel.user_id == user_id)
            .order_by(StudySessionModel.started_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self.mapper.to_domain(model) for model in models]

    async def get_daily_study_minutes(
        self, user_id: UUID, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get total study minutes per day for the last N days.

        Returns:
            List of dicts: [{"date": date, "minutes": int}]
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Calculate duration as difference between ended_at and started_at,
        # OR use pomodoros * duration if available?
        # The model has `pomodoro_duration_minutes` and `pomodoros_completed`.
        # But checking `ended_at - started_at` is more accurate for total time if recorded.
        # Let's stick to a simpler metric if available or count pomodoros.
        # Actually, `pomodoros_completed * pomodoro_duration_minutes` is a good proxy for focused time.

        stmt = (
            select(
                func.date(StudySessionModel.started_at).label("session_date"),
                func.sum(
                    StudySessionModel.pomodoros_completed *
                    StudySessionModel.pomodoro_duration_minutes
                ).label("total_minutes")
            )
            .where(
                StudySessionModel.user_id == user_id,
                StudySessionModel.started_at >= start_date
            )
            .group_by("session_date")
            .order_by("session_date")
        )

        result = await self.session.execute(stmt)

        stats = []
        for row in result:
            stats.append({
                "date": row.session_date,
                "minutes": row.total_minutes or 0
            })

        return stats

    async def get_total_study_minutes(self, user_id: UUID) -> int:
        """Get total lifetime study minutes"""
        stmt = (
            select(
                func.sum(
                    StudySessionModel.pomodoros_completed *
                    StudySessionModel.pomodoro_duration_minutes
                )
            )
            .where(StudySessionModel.user_id == user_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar() or 0
