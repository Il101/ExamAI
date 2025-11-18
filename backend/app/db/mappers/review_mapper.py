from typing import cast
from app.domain.review import ReviewItem, CardState, Rating
from app.db.models.review import ReviewItemModel


class ReviewItemMapper:
    """Maps between ReviewItem domain entity and ReviewItemModel DB model"""
    
    @staticmethod
    def to_domain(model: ReviewItemModel) -> ReviewItem:
        """Convert DB model to domain entity"""
        return ReviewItem(
            id=model.id,
            topic_id=model.topic_id,
            user_id=model.user_id,
            question=model.question,
            answer=model.answer,
            stability=model.stability,
            difficulty=model.difficulty,
            elapsed_days=model.elapsed_days,
            scheduled_days=model.scheduled_days,
            reps=model.reps,
            lapses=model.lapses,
            state=cast(CardState, model.state),
            next_review_date=model.next_review_date,
            last_reviewed_at=model.last_reviewed_at,
            last_review_rating=cast(Rating, model.last_review_rating) if model.last_review_rating is not None else None,
            created_at=model.created_at,
        )
    
    @staticmethod
    def to_model(domain: ReviewItem) -> ReviewItemModel:
        """Convert domain entity to DB model"""
        return ReviewItemModel(
            id=domain.id,
            topic_id=domain.topic_id,
            user_id=domain.user_id,
            question=domain.question,
            answer=domain.answer,
            stability=domain.stability,
            difficulty=domain.difficulty,
            elapsed_days=domain.elapsed_days,
            scheduled_days=domain.scheduled_days,
            reps=domain.reps,
            lapses=domain.lapses,
            state=domain.state,
            next_review_date=domain.next_review_date,
            last_reviewed_at=domain.last_reviewed_at,
            last_review_rating=domain.last_review_rating,
            created_at=domain.created_at,
        )
    
    @staticmethod
    def update_model(model: ReviewItemModel, domain: ReviewItem) -> ReviewItemModel:
        """Update existing DB model with domain data"""
        model.question = domain.question
        model.answer = domain.answer
        model.stability = domain.stability
        model.difficulty = domain.difficulty
        model.elapsed_days = domain.elapsed_days
        model.scheduled_days = domain.scheduled_days
        model.reps = domain.reps
        model.lapses = domain.lapses
        model.state = domain.state
        model.next_review_date = domain.next_review_date
        model.last_reviewed_at = domain.last_reviewed_at
        model.last_review_rating = domain.last_review_rating
        
        return model
