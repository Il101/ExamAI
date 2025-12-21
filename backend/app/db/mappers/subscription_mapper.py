from typing import cast

from app.db.models.subscription import SubscriptionModel
from app.domain.subscription import Subscription, SubscriptionStatus


class SubscriptionMapper:
    """Maps between Subscription domain entity and SubscriptionModel DB model"""

    @staticmethod
    def to_domain(model: SubscriptionModel) -> Subscription:
        """Convert DB model to domain entity"""
        return Subscription(
            id=model.id,
            user_id=model.user_id,
            plan_type=cast(str, model.plan_type),
            status=cast(SubscriptionStatus, model.status),
            current_period_start=model.current_period_start,
            current_period_end=model.current_period_end,
            external_subscription_id=model.external_subscription_id,
            external_customer_id=model.external_customer_id,
            cancel_at_period_end=model.cancel_at_period_end,
            canceled_at=model.canceled_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(domain: Subscription) -> SubscriptionModel:
        """Convert domain entity to DB model"""
        return SubscriptionModel(
            id=domain.id,
            user_id=domain.user_id,
            plan_type=domain.plan_type,
            status=domain.status,
            current_period_start=domain.current_period_start,
            current_period_end=domain.current_period_end,
            external_subscription_id=domain.external_subscription_id,
            external_customer_id=domain.external_customer_id,
            cancel_at_period_end=domain.cancel_at_period_end,
            canceled_at=domain.canceled_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    @staticmethod
    def update_model(
        model: SubscriptionModel, domain: Subscription
    ) -> SubscriptionModel:
        """Update existing DB model with domain data"""
        model.plan_type = domain.plan_type
        model.status = domain.status
        model.current_period_start = domain.current_period_start
        model.current_period_end = domain.current_period_end
        model.external_subscription_id = domain.external_subscription_id
        model.external_customer_id = domain.external_customer_id
        model.cancel_at_period_end = domain.cancel_at_period_end
        model.canceled_at = domain.canceled_at
        model.updated_at = domain.updated_at

        return model
