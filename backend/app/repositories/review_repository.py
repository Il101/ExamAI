from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.review import ReviewItem
from app.db.models.review import ReviewItemModel
from app.db.mappers.review_mapper import ReviewItemMapper
from app.repositories.base import BaseRepository


class ReviewItemRepository(BaseRepository[ReviewItem, ReviewItemModel]):
    """Repository for ReviewItem entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewItemModel, ReviewItemMapper)
    
    async def list_due_by_user(
        self,
        user_id: UUID,
        limit: int = 100
    ) -> List[ReviewItem]:
        """Get review items due for review"""
        now = datetime.utcnow()
        
        stmt = select(ReviewItemModel).where(
            ReviewItemModel.user_id == user_id,
            ReviewItemModel.next_review_date <= now
        ).order_by(
            ReviewItemModel.next_review_date.asc()
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
    
    async def list_by_topic(self, topic_id: UUID) -> List[ReviewItem]:
        """Get all review items for a topic"""
        stmt = select(ReviewItemModel).where(
            ReviewItemModel.topic_id == topic_id
        ).order_by(ReviewItemModel.created_at.asc())
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
    
    async def count_due_by_user(self, user_id: UUID) -> int:
        """Count items due for review"""
        now = datetime.utcnow()
        
        stmt = select(func.count()).select_from(ReviewItemModel).where(
            ReviewItemModel.user_id == user_id,
            ReviewItemModel.next_review_date <= now
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
