from typing import cast

from app.db.models.topic import TopicModel
from app.domain.topic import Topic, TopicStatus


class TopicMapper:
    """Mapper between Topic domain entity and TopicModel"""

    @staticmethod
    def to_domain(model: TopicModel) -> Topic:
        """Convert DB model to domain entity"""
        return Topic(
            id=model.id,
            exam_id=model.exam_id,
            user_id=model.user_id,
            topic_name=model.topic_name,
            content=model.content,
            file_context=model.file_context,
            status=cast(TopicStatus, model.status),
            order_index=model.order_index,
            generation_priority=model.generation_priority,
            difficulty_level=model.difficulty_level,
            created_at=model.created_at,
            updated_at=model.updated_at,
            estimated_study_minutes=model.estimated_study_minutes,
        )

    @staticmethod
    def to_model(entity: Topic) -> TopicModel:
        """Convert domain entity to DB model"""
        return TopicModel(
            id=entity.id,
            exam_id=entity.exam_id,
            user_id=entity.user_id,
            topic_name=entity.topic_name,
            content=entity.content,
            file_context=entity.file_context,
            status=entity.status,
            order_index=entity.order_index,
            generation_priority=entity.generation_priority,
            difficulty_level=entity.difficulty_level,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            estimated_study_minutes=entity.estimated_study_minutes,
        )

    @staticmethod
    def update_model(model: TopicModel, entity: Topic) -> TopicModel:
        """Update existing DB model with domain data"""
        model.topic_name = entity.topic_name
        model.content = entity.content
        model.file_context = entity.file_context
        model.status = entity.status
        model.order_index = entity.order_index
        model.generation_priority = entity.generation_priority
        model.difficulty_level = entity.difficulty_level
        model.updated_at = entity.updated_at
        model.estimated_study_minutes = entity.estimated_study_minutes
        
        return model
