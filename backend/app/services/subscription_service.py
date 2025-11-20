from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

from app.domain.subscription import Subscription
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.stripe_service import StripeService
from app.core.config import settings


class SubscriptionService:
    """
    Service for subscription management.
    Coordinates between StripeService and SubscriptionRepository.
    """

    def __init__(
        self, subscription_repo: SubscriptionRepository, stripe_service: StripeService
    ):
        self.subscription_repo = subscription_repo
        self.stripe_service = stripe_service

    def get_available_plans(self) -> List[Dict[str, Any]]:
        """
        Get available subscription plans.

        Returns:
            List of plan dictionaries
        """
        return [
            {
                "id": "free",
                "name": "Free",
                "price": {"amount": 0, "currency": "EUR", "billing_period": None},
                "features": {
                    "max_exams": 3,
                    "ai_model": "gemini-2.0-flash-lite",
                    "advanced_analytics": False,
                    "export": False,
                },
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": {"amount": 9.99, "currency": "EUR", "billing_period": "month"},
                "stripe_price_id": settings.STRIPE_PRICE_ID_PRO,
                "features": {
                    "max_exams": 20,
                    "ai_model": "gemini-2.0-flash-exp",
                    "advanced_analytics": True,
                    "export": True,
                },
                "popular": True,
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": {
                    "amount": 19.99,
                    "currency": "EUR",
                    "billing_period": "month",
                },
                "stripe_price_id": settings.STRIPE_PRICE_ID_PREMIUM,
                "features": {
                    "max_exams": None,  # Unlimited
                    "ai_model": "gemini-2.0-flash-exp",
                    "advanced_analytics": True,
                    "export": True,
                    "priority_support": True,
                },
            },
        ]

    async def get_user_subscription(self, user_id: UUID) -> Subscription:
        """
        Get user's subscription (or create free tier if none exists).

        Args:
            user_id: User UUID

        Returns:
            Subscription object
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)

        if subscription is None:
            # Create free tier subscription
            subscription = Subscription(
                user_id=user_id,
                plan_type="free",
                status="active",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow()
                + timedelta(days=36500),  # 100 years (permanent)
            )
            subscription = await self.subscription_repo.create(subscription)

        return subscription

    async def create_checkout_session(
        self,
        user_id: UUID,
        user_email: str,
        plan_type: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for subscription upgrade.

        Args:
            user_id: User UUID
            user_email: User email
            plan_type: 'pro' or 'premium'
            success_url: Redirect URL after success
            cancel_url: Redirect URL if canceled

        Returns:
            Dict with checkout_url
        """
        # Get existing subscription
        subscription = await self.get_user_subscription(user_id)

        # Create Stripe checkout
        checkout = self.stripe_service.create_checkout_session(
            user_id=user_id,
            user_email=user_email,
            plan_type=plan_type,
            success_url=success_url,
            cancel_url=cancel_url,
            stripe_customer_id=subscription.stripe_customer_id,
        )

        # Update subscription with customer ID if new
        if not subscription.stripe_customer_id:
            subscription.stripe_customer_id = checkout["customer_id"]
            await self.subscription_repo.update(subscription)

        return {"checkout_url": checkout["checkout_url"]}

    async def handle_subscription_created(self, stripe_subscription: Dict[str, Any]):
        """
        Handle Stripe subscription.created webhook event.

        Args:
            stripe_subscription: Stripe subscription object
        """
        user_id = UUID(stripe_subscription["metadata"]["user_id"])
        plan_type = stripe_subscription["metadata"]["plan_type"]

        subscription = await self.subscription_repo.get_by_user_id(user_id)

        if subscription:
            # Update existing subscription
            subscription.plan_type = plan_type
            subscription.status = "active"
            subscription.stripe_subscription_id = stripe_subscription["id"]
            subscription.stripe_customer_id = stripe_subscription["customer"]
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription["current_period_start"]
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription["current_period_end"]
            )
            subscription.cancel_at_period_end = stripe_subscription.get(
                "cancel_at_period_end", False
            )
            subscription.updated_at = datetime.utcnow()

            await self.subscription_repo.update(subscription)

    async def handle_subscription_updated(self, stripe_subscription: Dict[str, Any]):
        """
        Handle Stripe subscription.updated webhook event.
        """
        subscription = await self.subscription_repo.get_by_stripe_subscription_id(
            stripe_subscription["id"]
        )

        if subscription:
            subscription.status = stripe_subscription["status"]
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription["current_period_end"]
            )
            subscription.cancel_at_period_end = stripe_subscription.get(
                "cancel_at_period_end", False
            )
            subscription.updated_at = datetime.utcnow()

            await self.subscription_repo.update(subscription)

    async def handle_subscription_deleted(self, stripe_subscription: Dict[str, Any]):
        """
        Handle Stripe subscription.deleted webhook event.
        """
        subscription = await self.subscription_repo.get_by_stripe_subscription_id(
            stripe_subscription["id"]
        )

        if subscription:
            # Downgrade to free tier
            subscription.plan_type = "free"
            subscription.status = "canceled"
            subscription.stripe_subscription_id = None
            subscription.canceled_at = datetime.utcnow()
            subscription.updated_at = datetime.utcnow()

            await self.subscription_repo.update(subscription)

    async def cancel_subscription(self, user_id: UUID) -> Subscription:
        """
        Cancel user's subscription (at period end).

        Args:
            user_id: User UUID

        Returns:
            Updated subscription
        """
        subscription = await self.get_user_subscription(user_id)

        if subscription.stripe_subscription_id:
            # Cancel in Stripe
            self.stripe_service.cancel_subscription(
                subscription.stripe_subscription_id, at_period_end=True
            )

            # Update local record
            subscription.cancel_at_period_end = True
            subscription.canceled_at = datetime.utcnow()
            subscription.updated_at = datetime.utcnow()

            await self.subscription_repo.update(subscription)

        return subscription

    async def reactivate_subscription(self, user_id: UUID) -> Subscription:
        """
        Reactivate a subscription that was set to cancel.

        Args:
            user_id: User UUID

        Returns:
            Updated subscription
        """
        subscription = await self.get_user_subscription(user_id)

        if subscription.stripe_subscription_id and subscription.cancel_at_period_end:
            # Reactivate in Stripe
            self.stripe_service.reactivate_subscription(
                subscription.stripe_subscription_id
            )

            # Update local record
            subscription.cancel_at_period_end = False
            subscription.updated_at = datetime.utcnow()

            await self.subscription_repo.update(subscription)

        return subscription

    def get_customer_portal_url(self, stripe_customer_id: str, return_url: str) -> str:
        """
        Get Stripe Customer Portal URL.

        Args:
            stripe_customer_id: Stripe customer ID
            return_url: URL to return to

        Returns:
            Portal URL
        """
        return self.stripe_service.create_customer_portal_session(
            stripe_customer_id, return_url
        )
