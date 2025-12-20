from app.db.models.push_subscription import PushSubscriptionModel
from app.domain.push import PushSubscription


class PushSubscriptionMapper:
    """Maps between PushSubscription domain entity and PushSubscriptionModel DB model"""

    @staticmethod
    def to_domain(model: PushSubscriptionModel) -> PushSubscription:
        """Convert DB model to domain entity"""
        return PushSubscription(
            id=model.id,
            user_id=model.user_id,
            endpoint=model.endpoint,
            p256dh=model.p256dh,
            auth=model.auth,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(domain: PushSubscription) -> PushSubscriptionModel:
        """Convert domain entity to DB model"""
        return PushSubscriptionModel(
            id=domain.id,
            user_id=domain.user_id,
            endpoint=domain.endpoint,
            p256dh=domain.p256dh,
            auth=domain.auth,
            created_at=domain.created_at,
        )

    @staticmethod
    def update_model(model: PushSubscriptionModel, domain: PushSubscription) -> PushSubscriptionModel:
        """Update existing DB model with domain data"""
        model.endpoint = domain.endpoint
        model.p256dh = domain.p256dh
        model.auth = domain.auth
        return model
