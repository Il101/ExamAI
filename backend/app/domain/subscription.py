# backend/app/domain/subscription.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

SubscriptionStatus = Literal["active", "canceled", "past_due", "trialing"]


@dataclass
class Subscription:
    """
    User subscription domain entity.
    Manages billing cycles, plan changes, and access control.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)

    plan_type: Literal["free", "pro", "premium"] = "free"
    status: SubscriptionStatus = "active"

    # Billing cycle
    current_period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    current_period_end: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )

    # External billing IDs (Stripe)
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

    # Cancel info
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Business logic

    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == "active" and datetime.now(timezone.utc) <= self.current_period_end

    def can_access_feature(self, feature: str) -> bool:
        """Check feature access based on plan"""
        features_by_plan = {
            "free": ["basic_exams", "3_concurrent_exams"],
            "pro": [
                "basic_exams",
                "20_concurrent_exams",
                "advanced_analytics",
                "export_pdf",
            ],
            "premium": [
                "basic_exams",
                "unlimited_exams",
                "advanced_analytics",
                "export_pdf",
                "priority_support",
            ],
        }

        return feature in features_by_plan.get(self.plan_type, [])

    def upgrade(self, new_plan: Literal["pro", "premium"]):
        """Upgrade subscription"""
        plan_hierarchy = {"free": 0, "pro": 1, "premium": 2}

        if plan_hierarchy[new_plan] <= plan_hierarchy[self.plan_type]:
            raise ValueError("Can only upgrade to higher plan")

        self.plan_type = new_plan
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self, immediate: bool = False):
        """Cancel subscription"""
        if immediate:
            self.status = "canceled"
            self.current_period_end = datetime.now(timezone.utc)
        else:
            self.cancel_at_period_end = True

        self.canceled_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def renew(self, duration_days: int = 30):
        """Renew subscription for next period"""
        if self.status != "active":
            raise ValueError("Can only renew active subscriptions")

        self.current_period_start = self.current_period_end
        self.current_period_end = self.current_period_start + timedelta(
            days=duration_days
        )
        self.updated_at = datetime.now(timezone.utc)

    def days_until_renewal(self) -> int:
        """Days until next billing"""
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)
