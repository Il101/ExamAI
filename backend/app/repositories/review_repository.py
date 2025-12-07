from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import func, select, case, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.review_mapper import ReviewItemMapper
from app.db.models.review import ReviewItemModel
from app.domain.review import ReviewItem
from app.repositories.base import BaseRepository


class ReviewItemRepository(BaseRepository[ReviewItem, ReviewItemModel]):
    """Repository for ReviewItem entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewItemModel, ReviewItemMapper)

    async def list_due_by_user(
        self, 
        user_id: UUID, 
        limit: int = 100, 
        exam_id: UUID | None = None,
        topic_id: UUID | None = None
    ) -> List[ReviewItem]:
        """Get review items due for review"""
        from datetime import timezone
        from app.db.models.topic import TopicModel

        now = datetime.now(timezone.utc)

        stmt = (
            select(ReviewItemModel)
            .join(TopicModel, ReviewItemModel.topic_id == TopicModel.id)
            .where(
                ReviewItemModel.user_id == user_id,
                ReviewItemModel.next_review_date <= now,
            )
        )

        if topic_id:
            stmt = stmt.where(ReviewItemModel.topic_id == topic_id)
        
        if exam_id:
            stmt = stmt.where(TopicModel.exam_id == exam_id)

        stmt = (
            stmt
            .order_by(ReviewItemModel.next_review_date.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self.mapper.to_domain(model) for model in models]

    async def list_by_topic(self, topic_id: UUID) -> List[ReviewItem]:
        """Get all review items for a topic"""
        stmt = (
            select(ReviewItemModel)
            .where(ReviewItemModel.topic_id == topic_id)
            .order_by(ReviewItemModel.created_at.asc())
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self.mapper.to_domain(model) for model in models]

    async def count_due_by_user(self, user_id: UUID) -> int:
        """Count items due for review"""
        from datetime import timezone
        now = datetime.now(timezone.utc)

        stmt = (
            select(func.count())
            .select_from(ReviewItemModel)
            .where(
                ReviewItemModel.user_id == user_id,
                ReviewItemModel.next_review_date <= now,
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_daily_activity(
        self, user_id: UUID, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get review counts per day for the last N days.

        Returns:
            List of dicts: [{"date": date, "count": int, "learned": int}]
        """
        # Since we don't have a separate ReviewLog table, we can only approximate
        # activity based on `last_reviewed_at`. This is a limitation of the current schema.
        # A proper implementation would require a `review_logs` table.
        # For now, we will just return what we can from the current state,
        # effectively showing "items reviewed recently".
        #
        # NOTE: To fix this properly, we would need to introduce a ReviewLog model.
        # Given the scope, we will implement a query that assumes `last_reviewed_at`
        # is the primary signal for "activity". This will undercount multiple reviews per day.

        from datetime import timezone
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                func.date(ReviewItemModel.last_reviewed_at).label("review_date"),
                func.count().label("review_count"),
                func.sum(case((ReviewItemModel.state == 'review', 1), else_=0)).label("learned_count")
            )
            .where(
                ReviewItemModel.user_id == user_id,
                ReviewItemModel.last_reviewed_at >= start_date
            )
            .group_by("review_date")
            .order_by("review_date")
        )

        result = await self.session.execute(stmt)

        activity = []
        for row in result:
            activity.append({
                "date": row.review_date,
                "count": row.review_count,
                "learned": row.learned_count or 0
            })

        return activity

    async def count_total_learned(self, user_id: UUID) -> int:
        """Count total items in 'review' or 'relearning' state (implied learned)"""
        stmt = (
            select(func.count())
            .select_from(ReviewItemModel)
            .where(
                ReviewItemModel.user_id == user_id,
                ReviewItemModel.state.in_(['review', 'relearning'])
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
