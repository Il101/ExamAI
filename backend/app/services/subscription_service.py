from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.domain.subscription import Subscription
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.lemonsqueezy_service import LemonSqueezyService
from app.core.config import settings


class SubscriptionService:
    """
    Service for subscription management.
    Coordinates between LemonSqueezyService and SubscriptionRepository.
    """

    def __init__(
        self, subscription_repo: SubscriptionRepository, lemonsqueezy_service: LemonSqueezyService
    ):
        self.subscription_repo = subscription_repo
        self.lemonsqueezy_service = lemonsqueezy_service

    def get_available_plans(self) -> List[Dict[str, Any]]:
        """
        Get available subscription plans using centralized config.

        Returns:
            List of plan dictionaries
        """
        from app.core.limits_config import PLAN_LIMITS, PLAN_PRICING
        
        return [
            {
                "id": "free",
                "name": "Starter",
                "description": "Get started with AI-powered studying",
                "price": {
                    "monthly": {"amount": PLAN_PRICING["free"]["monthly"], "currency": "EUR"},
                    "yearly": {"amount": PLAN_PRICING["free"]["yearly"], "currency": "EUR"},
                    "amount": 0, "currency": "EUR", "billing_period": None
                },
                "limits": PLAN_LIMITS["free"],
                "features": {
                    "spaced_repetition": True,
                    "ai_tutor": True,
                    "advanced_analytics": False,
                    "export_pdf": False,
                    "priority_generation": False,
                    "priority_support": False,
                },
            },
            {
                "id": "pro",
                "name": "Pro",
                "description": "For serious students who want more",
                "price": {
                    "monthly": {"amount": PLAN_PRICING["pro"]["monthly"], "currency": "EUR"},
                    "yearly": {"amount": PLAN_PRICING["pro"]["yearly"], "currency": "EUR"},
                },
                "lemonsqueezy_variant_id_monthly": settings.LEMON_SQUEEZY_VARIANT_ID_PRO,
                "lemonsqueezy_variant_id_yearly": settings.LEMON_SQUEEZY_VARIANT_ID_PRO_YEARLY,
                "limits": PLAN_LIMITS["pro"],
                "features": {
                    "spaced_repetition": True,
                    "ai_tutor": True,
                    "advanced_analytics": True,
                    "export_pdf": True,
                    "priority_generation": False,
                    "priority_support": False,
                },
                "popular": True,
            },
            {
                "id": "premium",
                "name": "Premium",
                "description": "Unlimited power for power users",
                "price": {
                    "monthly": {"amount": PLAN_PRICING["premium"]["monthly"], "currency": "EUR"},
                    "yearly": {"amount": PLAN_PRICING["premium"]["yearly"], "currency": "EUR"},
                },
                "lemonsqueezy_variant_id_monthly": settings.LEMON_SQUEEZY_VARIANT_ID_PREMIUM,
                "lemonsqueezy_variant_id_yearly": settings.LEMON_SQUEEZY_VARIANT_ID_PREMIUM_YEARLY,
                "limits": PLAN_LIMITS["premium"],
                "features": {
                    "spaced_repetition": True,
                    "ai_tutor": True,
                    "advanced_analytics": True,
                    "export_pdf": True,
                    "priority_generation": True,
                    "priority_support": True,
                },
            },
            {
                "id": "team",
                "name": "Team",
                "description": "Perfect for study groups of up to 5",
                "price": {
                    "monthly": {"amount": PLAN_PRICING["team"]["monthly"], "currency": "EUR"},
                    "yearly": {"amount": PLAN_PRICING["team"]["yearly"], "currency": "EUR"},
                },
                "lemonsqueezy_variant_id_monthly": settings.LEMON_SQUEEZY_VARIANT_ID_TEAM,
                "lemonsqueezy_variant_id_yearly": settings.LEMON_SQUEEZY_VARIANT_ID_TEAM_YEARLY,
                "limits": PLAN_LIMITS["team"],
                "features": {
                    "spaced_repetition": True,
                    "ai_tutor": True,
                    "advanced_analytics": True,
                    "export_pdf": True,
                    "priority_generation": True,
                    "priority_support": True,
                    "team_management": True,
                },
            },
        ]

    async def get_user_subscription(self, user_id: UUID) -> Subscription:
        """
        Get user's subscription (or create free tier if none exists).
        """
        subscription = await self.subscription_repo.get_by_user_id(user_id)

        if subscription is None:
            # Create free tier subscription
            subscription = Subscription(
                user_id=user_id,
                plan_type="free",
                status="active",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc)
                + timedelta(days=36500),  # 100 years
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
        billing_period: str = "monthly",
    ) -> Dict[str, Any]:
        """
        Create Lemon Squeezy checkout session for subscription upgrade.
        """
        # Get existing subscription
        subscription = await self.get_user_subscription(user_id)

        # Create Lemon Squeezy checkout
        checkout = self.lemonsqueezy_service.create_checkout_session(
            user_id=user_id,
            user_email=user_email,
            plan_type=plan_type,
            success_url=success_url,
            cancel_url=cancel_url,
            billing_period=billing_period,
            external_customer_id=subscription.external_customer_id,
        )

        return {"checkout_url": checkout["checkout_url"]}

    async def handle_subscription_created(self, payload: Dict[str, Any]):
        """
        Handle Lemon Squeezy subscription.created webhook event.
        """
        attributes = payload["data"]["attributes"]
        custom_data = attributes.get("custom_data", {})
        
        user_id_str = custom_data.get("user_id")
        if not user_id_str:
            return
            
        user_id = UUID(user_id_str)
        plan_type = custom_data.get("plan_type", "pro")

        subscription = await self.subscription_repo.get_by_user_id(user_id)

        if subscription:
            subscription.plan_type = plan_type
            subscription.status = attributes["status"]
            subscription.external_subscription_id = str(payload["data"]["id"])
            subscription.external_customer_id = str(attributes["customer_id"])
            
            # Lemon Squeezy provides ends_at or renews_at
            if attributes.get("renews_at"):
                subscription.current_period_end = datetime.fromisoformat(
                    attributes["renews_at"].replace("Z", "+00:00")
                )
            
            subscription.updated_at = datetime.now(timezone.utc)
            await self.subscription_repo.update(subscription)

    async def handle_subscription_updated(self, payload: Dict[str, Any]):
        """
        Handle Lemon Squeezy subscription.updated webhook event.
        """
        attributes = payload["data"]["attributes"]
        subscription = await self.subscription_repo.get_by_external_subscription_id(
            str(payload["data"]["id"])
        )

        if subscription:
            subscription.status = attributes["status"]
            if attributes.get("renews_at"):
                subscription.current_period_end = datetime.fromisoformat(
                    attributes["renews_at"].replace("Z", "+00:00")
                )
            
            subscription.cancel_at_period_end = attributes.get("cancelled", False)
            subscription.updated_at = datetime.now(timezone.utc)

            await self.subscription_repo.update(subscription)

    async def handle_subscription_cancelled(self, payload: Dict[str, Any]):
        """
        Handle Lemon Squeezy subscription.cancelled (expired) event.
        """
        subscription = await self.subscription_repo.get_by_external_subscription_id(
            str(payload["data"]["id"])
        )

        if subscription:
            # Downgrade to free tier
            subscription.plan_type = "free"
            subscription.status = "expired"
            subscription.external_subscription_id = None
            subscription.canceled_at = datetime.now(timezone.utc)
            subscription.updated_at = datetime.now(timezone.utc)

            await self.subscription_repo.update(subscription)

    async def cancel_subscription(self, user_id: UUID) -> Subscription:
        """
        Cancel user's subscription in Lemon Squeezy.
        """
        subscription = await self.get_user_subscription(user_id)

        if subscription.external_subscription_id:
            # Cancel in Lemon Squeezy
            self.lemonsqueezy_service.cancel_subscription(
                subscription.external_subscription_id
            )

            # Update local record
            subscription.cancel_at_period_end = True
            subscription.canceled_at = datetime.now(timezone.utc)
            subscription.updated_at = datetime.now(timezone.utc)

            await self.subscription_repo.update(subscription)

        return subscription
