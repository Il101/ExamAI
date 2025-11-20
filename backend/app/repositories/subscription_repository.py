from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.subscription_mapper import SubscriptionMapper
from app.db.models.subscription import SubscriptionModel
from app.domain.subscription import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription, SubscriptionModel]):
    """Repository for Subscription entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SubscriptionModel, SubscriptionMapper)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Subscription]:
        """Get subscription by user ID"""
        stmt = select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self.mapper.to_domain(model)

    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID"""
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.stripe_subscription_id == stripe_subscription_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self.mapper.to_domain(model)

    async def get_by_stripe_customer_id(
        self, stripe_customer_id: str
    ) -> Optional[Subscription]:
        """Get subscription by Stripe customer ID"""
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.stripe_customer_id == stripe_customer_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self.mapper.to_domain(model)
