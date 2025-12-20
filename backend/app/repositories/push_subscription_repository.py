from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.push_subscription_mapper import PushSubscriptionMapper
from app.db.models.push_subscription import PushSubscriptionModel
from app.domain.push import PushSubscription
from app.repositories.base import BaseRepository


class PushSubscriptionRepository(BaseRepository[PushSubscription, PushSubscriptionModel]):
    """Repository for PushSubscription entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PushSubscriptionModel, PushSubscriptionMapper)

    async def get_by_user_id(self, user_id: UUID) -> List[PushSubscription]:
        """Get all subscriptions for a specific user"""
        stmt = select(PushSubscriptionModel).where(PushSubscriptionModel.user_id == user_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self.mapper.to_domain(m) for m in models]

    async def get_by_endpoint(self, endpoint: str) -> Optional[PushSubscription]:
        """Get subscription by endpoint (to detect duplicates)"""
        stmt = select(PushSubscriptionModel).where(PushSubscriptionModel.endpoint == endpoint)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self.mapper.to_domain(model)

    async def delete_by_endpoint(self, endpoint: str) -> bool:
        """Remove a subscription by its endpoint"""
        stmt = select(PushSubscriptionModel).where(PushSubscriptionModel.endpoint == endpoint)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return False
        
        await self.session.delete(model)
        await self.session.commit()
        return True
