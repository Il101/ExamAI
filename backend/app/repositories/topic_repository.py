from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.topic_mapper import TopicMapper
from app.db.models.topic import TopicModel
from app.domain.topic import Topic
from app.repositories.base import BaseRepository


class TopicRepository(BaseRepository[Topic, TopicModel]):
    """Repository for Topic entities"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, TopicModel, TopicMapper)

    async def get_by_exam_id(self, exam_id: UUID) -> List[Topic]:
        """Get all topics for an exam ordered by index with flashcard counts"""
        from sqlalchemy import func
        from app.db.models.review import ReviewItemModel

        stmt = (
            select(TopicModel, func.count(ReviewItemModel.id).label("flashcard_count"))
            .outerjoin(ReviewItemModel, TopicModel.id == ReviewItemModel.topic_id)
            .where(TopicModel.exam_id == exam_id)
            .group_by(TopicModel.id)
            .order_by(TopicModel.order_index)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        # Map models and attach count manually (since it's not a model field)
        topics = []
        for model, count in rows:
            # We treat flashcard_count as a dynamic attribute on the model instance
            # The mapper will read it via getattr(model, "flashcard_count", 0)
            setattr(model, "flashcard_count", count)
            topics.append(self.mapper.to_domain(model))

        return topics

    async def bulk_create(self, topics: List[Topic]) -> List[Topic]:
        """Create multiple topics at once"""
        models = [self.mapper.to_model(t) for t in topics]
        self.session.add_all(models)
        await self.session.flush()

        # Refresh all models to get IDs and timestamps
        for model in models:
            await self.session.refresh(model)

        return [self.mapper.to_domain(m) for m in models]
