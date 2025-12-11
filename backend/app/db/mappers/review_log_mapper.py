from app.db.models.review_log import ReviewLogModel
from app.domain.review_log import ReviewLog


class ReviewLogMapper:
    """Maps between ReviewLog domain entity and ReviewLogModel DB model"""

    @staticmethod
    def to_domain(model: ReviewLogModel) -> ReviewLog:
        """Convert DB model to domain entity"""
        return ReviewLog(
            id=model.id,
            user_id=model.user_id,
            review_item_id=model.review_item_id,
            rating=model.rating,
            review_time=model.review_time,
            interval_days=model.interval_days,
            scheduled_days=model.scheduled_days,
            stability=model.stability,
            difficulty=model.difficulty,
            review_duration_ms=model.review_duration_ms,
        )

    @staticmethod
    def to_model(domain: ReviewLog) -> ReviewLogModel:
        """Convert domain entity to DB model"""
        return ReviewLogModel(
            id=domain.id,
            user_id=domain.user_id,
            review_item_id=domain.review_item_id,
            rating=domain.rating,
            review_time=domain.review_time,
            interval_days=domain.interval_days,
            scheduled_days=domain.scheduled_days,
            stability=domain.stability,
            difficulty=domain.difficulty,
            review_duration_ms=domain.review_duration_ms,
        )
