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
        """Get all topics for an exam ordered by index"""
        stmt = (
            select(TopicModel)
            .where(TopicModel.exam_id == exam_id)
            .order_by(TopicModel.order_index)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self.mapper.to_domain(m) for m in models]

    async def bulk_create(self, topics: List[Topic]) -> List[Topic]:
        """Create multiple topics at once"""
        models = [self.mapper.to_model(t) for t in topics]
        self.session.add_all(models)
        await self.session.flush()

        # Refresh all models to get IDs and timestamps
        for model in models:
            await self.session.refresh(model)

        return [self.mapper.to_domain(m) for m in models]
